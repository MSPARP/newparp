import random
import uuid

from flask import g

from newparp.model import Chat
from newparp.model.connections import NewparpRedis, redis_chat_pool
from newparp.model.user_list import UserListStore, PingTimeoutException

def get_userlist(client, chat: Chat) -> UserListStore:
    client.get("/" + chat.url)
    user_list = UserListStore(NewparpRedis(connection_pool=redis_chat_pool), chat.id)
    return user_list

def test_join_leave(user_client, group_chat):
    user_list = get_userlist(user_client, group_chat)
    socket_id = str(uuid.uuid4())

    # Do some quick sanity checks to ensure that everything is empty
    assert user_list.session_has_open_socket(g.session_id, g.user_id) is False
    assert len(user_list.user_ids_online()) == 0
    assert user_list.socket_disconnect(socket_id, g.user_id) is False
    assert user_list.user_disconnect(g.user_id, g.user_id) is False

    # Socket join/leave process
    assert user_list.socket_join(socket_id, g.session_id, g.user_id) is True
    assert len(user_list.user_ids_online()) == 1
    assert user_list.socket_disconnect(socket_id, g.user_id) is True
    assert len(user_list.user_ids_online()) == 0

    # User should stop typing when they leave
    assert user_list.socket_join(socket_id, g.session_id, g.user_id) is True
    user_list.user_start_typing(g.user_id)
    assert len(user_list.user_numbers_typing()) == 1
    assert user_list.socket_disconnect(socket_id, g.user_id) is True
    assert len(user_list.user_numbers_typing()) == 0

    # [Kick, Ban] join/leave process
    assert user_list.socket_join(socket_id, g.session_id, g.user_id) is True
    assert len(user_list.user_ids_online()) == 1
    assert user_list.user_disconnect(g.user_id, g.user_id) is True
    assert len(user_list.user_ids_online()) == 0

    # User should stop typing when they leave
    assert user_list.socket_join(socket_id, g.session_id, g.user_id) is True
    user_list.user_start_typing(g.user_id)
    assert len(user_list.user_numbers_typing()) == 1
    assert user_list.user_disconnect(g.user_id, g.user_id) is True
    assert len(user_list.user_numbers_typing()) == 0


def test_typing(user_client, group_chat):
    USER_AMOUNT = 10
    users = sorted({random.randint(0, 100) for x in range(0, USER_AMOUNT)})

    user_list = get_userlist(user_client, group_chat)

    # Ensure that we are empty before doing anything
    assert len(user_list.user_numbers_typing()) == 0

    # Test start typing for a single user
    user_list.user_start_typing(users[0])
    assert [users[0]] == user_list.user_numbers_typing()
    assert len(user_list.user_numbers_typing()) == 1

    # Test start typing for all users
    [user_list.user_start_typing(x) for x in users]
    assert users == sorted(user_list.user_numbers_typing())

    # Test stop typing for all users
    [user_list.user_stop_typing(x) for x in users]
    assert len(user_list.user_numbers_typing()) == 0

def test_socket_timeout(user_client, group_chat):
    user_list = get_userlist(user_client, group_chat)
    socket_id = str(uuid.uuid4())

    assert user_list.socket_join(socket_id, g.session_id, g.user_id) is True
    assert user_list.socket_ping(socket_id) is None

    # Force expire the ping key
    user_list.redis.delete(user_list.session_key % (socket_id))
    try:
        assert user_list.socket_ping(socket_id)
        # Something is wrong if we are reaching this.
        assert False
    except PingTimeoutException:
        assert True

    assert len(user_list.inconsistent_entries()) == 1
