import json, time


class UserListStore(object):
    """
    Helper class for managing online state.

    Redis keys used for online state:
    * chat:<chat_id>:online - map of socket ids -> user ids
    * chat:<chat_id>:online:<socket_id> - string, with the session id that the
      socket belongs to. Has a TTL to allow reaping.
    * chat:<chat_id>:typing - set, with user numbers of people who are typing.
    """

    def __init__(self, redis, chat_id):
        self.redis   = redis
        self.chat_id = chat_id
        self.online_key  = "chat:%s:online"     % self.chat_id
        self.session_key = "chat:%s:online:%%s" % self.chat_id
        self.typing_key  = "chat:%s:typing"     % self.chat_id

    def socket_join(self, socket_id, session_id, user_id):
        """
        Joins a socket to a chat. Returns a boolean indicating whether or not
        the user's online state changed.
        """
        pipe = self.redis.pipeline()

        # Remember whether they're already online.
        pipe.hvals(self.online_key)

        # Queue their last_online update.
        # TODO make sure celery is reading this from the right redis instance
        pipe.hset("queue:usermeta", "chatuser:%s" % user_id, json.dumps({
            "last_online": str(time.time()),
            "chat_id": self.chat_id,
        }))

        # Add them to the online list.
        pipe.hset(self.online_key, socket_id, user_id)
        pipe.setex(self.session_key % socket_id, 30, session_id)

        result = pipe.execute()

        return str(user_id) not in result[0]

    socket_ping_script = """
        local user_id_from_chat = redis.call("hget", "chat:"..ARGV[1]..":online", ARGV[2])
        if not user_id_from_chat then return false end

        local session_id = redis.call("get", "chat:"..ARGV[1]..":online:"..ARGV[2])
        if not session_id then return false end

        redis.call("expire", "chat:"..ARGV[1]..":online:"..ARGV[2], 30)
        return true
    """

    def socket_ping(self, socket_id):
        """
        Bumps a socket's ping time to avoid timeouts. This raises
        PingTimeoutException if they've already timed out.
        """
        result = self.redis.eval(self.socket_ping_script, 0, self.chat_id, socket_id)
        if not result:
            raise PingTimeoutException

    def socket_disconnect(self, socket_id, user_number):
        """
        Removes a socket from a chat. Returns a boolean indicating whether the
        user's online state has changed.
        """
        pipe = self.redis.pipeline()
        pipe.hget(self.online_key, socket_id)
        pipe.hdel(self.online_key, socket_id)
        pipe.delete(self.session_key % socket_id)
        pipe.srem(self.typing_key, user_number)
        pipe.hvals(self.online_key)
        user_id, _, _, _, new_user_ids = pipe.execute()
        if not user_id:
            return False
        return user_id not in new_user_ids

    user_disconnect_script = """
        local had_online_socket = false
        local online_list = redis.call("hgetall", "chat:"..ARGV[1]..":online")
        if #online_list == 0 then return false end
        for i = 1, #online_list, 2 do
            local socket_id = online_list[i]
            local user_id = online_list[i+1]
            if user_id == ARGV[2] then
                redis.call("hdel", "chat:"..ARGV[1]..":online", socket_id)
                redis.call("del",  "chat:"..ARGV[1]..":online:"..socket_id)
                had_online_socket = true
            end
        end
        redis.call("hdel", "chat:"..ARGV[1]..":typing", ARGV[3])
        return had_online_socket
    """

    def user_disconnect(self, user_id, user_number):
        """
        Removes all of a user's sockets from a chat. Returns a boolean
        indicating whether the user's online state has changed.
        """
        result = self.redis.eval(user_disconnect_script, 0, self.chat_id, user_id, user_number)
        return bool(result)

    def user_ids_online(self):
        """Returns a set of user IDs who are online."""
        return set(int(_) for _ in self.redis.hvals(self.online_key))

    session_has_open_socket_script = """
        local online_list = redis.call("hgetall", "chat:"..ARGV[1]..":online")
        if #online_list == 0 then return false end
        for i = 1, #online_list, 2 do
            local socket_id = online_list[i]
            local user_id = online_list[i+1]
            local session_id = redis.call("get", "chat:"..ARGV[1]..":online:"..socket_id)
            if session_id == ARGV[2] then
                if user_id == ARGV[3] then
                    return true
                end
                return false
            end
        end
        return false
    """

    def session_has_open_socket(self, session_id, user_id):
        """
        Indicates whether there's an open socket matching the session ID and
        user ID.
        """
        result = self.redis.eval(self.session_has_open_socket_script, 0, self.chat_id, session_id, user_id)
        return bool(result)

    def user_start_typing(self, user_number):
        """
        Mark a user as typing. Returns a bool indicating whether the user's
        typing state has changed.
        """
        return bool(self.redis.sadd(self.typing_key, user_number))

    def user_stop_typing(self, user_number):
        """
        Mark a user as no longer typing. Returns a bool indicating whether the
        user's typing state has changed.
        """
        return bool(self.redis.srem(self.typing_key, user_number))

    def user_numbers_typing(self):
        """Returns a list of user numbers who are typing."""
        return list(int(_) for _ in self.redis.smembers(self.typing_key))

    # TODO manage kicking here too?


class PingTimeoutException(Exception): pass
