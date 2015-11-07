#!/usr/bin/python
import os

from alembic.config import Config
from alembic import command
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.orm.exc import NoResultFound

from charat2.model import Base, engine, SearchCharacter, SearchCharacterGroup, sm, AdminTier, AdminTierPermission

if __name__ == "__main__":

    inspector = Inspector.from_engine(engine)
    if "alembic_version" in inspector.get_table_names():
        raise Exception("Database has already been initialised. Use \"alembic upgrade head\" instead.")

    engine.echo = True
    Base.metadata.create_all(bind=engine)

    alembic_cfg = Config(os.path.dirname(os.path.realpath(__file__)) + "/../../alembic.ini")
    command.stamp(alembic_cfg, "head")

    # Initialise search characters if necessary.
    db = sm()
    try:
        special_other = db.query(SearchCharacterGroup).filter(SearchCharacterGroup.id == 1).one()
        print "Special/other group found."
    except NoResultFound:
        print "Special/other group not found, creating."
        special_other = SearchCharacterGroup(name="Special/other", order=1)
        db.add(special_other)
        db.flush()
    try:
        anonymous_other = db.query(SearchCharacter).filter(SearchCharacter.id == 1).one()
        print "Anon/other character found."
    except NoResultFound:
        print "Anon/other character not found, creating."
        special_other = SearchCharacter(group_id=1, order=1, title="Anonymous/other")
        db.add(special_other)
        db.flush()
    db.commit()

    # Initalise admin tiers if there are no tiers
    if not db.query(AdminTier).scalar():
        supertier = AdminTier(
            name='Hoofbeast tier'
        )
        db.add(supertier)
        db.commit()

        for permission in AdminTierPermission.permission.property.columns[0].type.enums:
            db.add(AdminTierPermission(
                admin_tier_id=supertier.id,
                permission=permission
            ))

        db.commit()
