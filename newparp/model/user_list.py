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
        self.typing_key = "chat:%s:typing" % self.chat_id

    def socket_join(self, socket_id):
        raise NotImplementedError

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

    def socket_disconnect(self, socket_id):
        raise NotImplementedError

    def user_disconnect(self, user_id):
        raise NotImplementedError

    def user_ids_online(self):
        raise NotImplementedError

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
