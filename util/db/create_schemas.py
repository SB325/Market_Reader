from sqlalchemy.schema import CreateSchema
from util.db.models.news import Base as News_Base
from util.db.conn import insert_engine

import os
db_schema = os.environ.get("DATABASE_SCHEMA")

engine = insert_engine()

def create_schemas():
    if not engine.dialect.has_schema(
        connection=engine.connect(),
        schema=db_schema,
        ):
        with engine.begin() as conn:
            conn.execute(CreateSchema(db_schema))
            conn.commit()

    with engine.connect() as conn:
        News_Base.metadata.create_all(engine)
        conn.commit()
        conn.close()
    engine.dispose()

if __name__ == "__main__":
    create_schemas()