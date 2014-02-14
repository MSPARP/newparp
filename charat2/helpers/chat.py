import json

def send_message(db, redis, message):
    db.add(message)
    db.flush()
    redis.publish("channel.%s" % message.chat_id, json.dumps({
        "messages": [message.to_dict()],
    }))
    db.commit()

