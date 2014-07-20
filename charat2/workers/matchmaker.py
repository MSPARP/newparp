#!/usr/bin/python

import time
import json

from random import shuffle
from redis import StrictRedis
from uuid import uuid4

from charat2.model import sm, SearchedChat
from charat2.model.connections import redis_pool

if __name__ == "__main__":
    db = sm()
    redis = StrictRedis(connection_pool=redis_pool)
    while True:

        print "MATCHING"

        searchers = redis.smembers("searchers")

        searcher_list = list(redis.smembers("searchers"))
        shuffle(searcher_list)
        # This is a crazy hack to pair up the searchers.
        for s1, s2 in zip(*(iter(searcher_list),) * 2):
            print "MATCHED", s1, s2
            new_url = str(uuid4()).replace("-", "")
            print "SENDING TO", new_url
            db.add(SearchedChat(url=new_url))
            db.commit()
            match_message = json.dumps({ "status": "matched", "url": new_url })
            redis.publish("searcher:%s" % s1, match_message)
            redis.publish("searcher:%s" % s2, match_message)
            searchers.remove(s1)
            searchers.remove(s2)

        # Reset the searcher list for the next iteration.
        redis.delete("searchers")
        for searcher in searchers:
            print "UNMATCHED", searcher
            redis.publish("searcher:%s" % searcher, "{ \"status\": \"unmatched\" }")

        time.sleep(10)

