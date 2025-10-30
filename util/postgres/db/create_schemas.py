import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../'))

from util.postgres.db.models.tickers import Base
from util.postgres.db.models.fundamentals import FundamentalsBase
from util.postgres.db.conn import insert_engine
from sqlalchemy.schema import CreateSchema
import pdb

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
        Base.metadata.create_all(engine)
        FundamentalsBase.metadata.create_all(engine)
        conn.commit()
        conn.close()
    engine.dispose()

if __name__ == "__main__":
    create_schemas()