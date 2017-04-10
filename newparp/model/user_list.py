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

    def socket_ping(self, socket_id):
        raise NotImplementedError

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

