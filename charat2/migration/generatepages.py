from charat2.model import sm, Chat
from charat2.tasks.background import generate_logpages

db = sm()

chats = db.query(Chat).order_by(Chat.id).all()

for chat in chats:
    generate_logpages.delay(chat.id)
