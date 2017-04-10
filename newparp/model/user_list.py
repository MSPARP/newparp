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
        raise NotImplementedError

    def user_stop_typing(self, user_number):
        raise NotImplementedError

    def user_numbers_typing(self):
        raise NotImplementedError

    # TODO manage kicking here too?

