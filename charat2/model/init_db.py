#!/usr/bin/python

from charat2.model import Base, engine

if __name__ == "__main__":
    engine.echo = True
    Base.metadata.create_all(bind=engine)
