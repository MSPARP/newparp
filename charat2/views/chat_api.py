from charat2.auth import user_chat_required

@user_chat_required
def messages():
    raise NotImplementedError

@user_chat_required
def send():
    raise NotImplementedError

@user_chat_required
def set_state():
    raise NotImplementedError

@user_chat_required
def set_group():
    raise NotImplementedError

@user_chat_required
def user_action():
    raise NotImplementedError

@user_chat_required
def set_flag():
    raise NotImplementedError

@user_chat_required
def set_topic():
    raise NotImplementedError

@user_chat_required
def save():
    raise NotImplementedError

@user_chat_required
def ping():
    raise NotImplementedError

@user_chat_required
def quit():
    raise NotImplementedError

