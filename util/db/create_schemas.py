from sqlalchemy.schema import CreateSchema
# from util.db.models.tickers import Base as Symbols_Base
from util.db.models.filings import Base as Filings_Base
from util.db.conn import insert_engine

import os
db_schema = os.environ.get("DATABASE_SCHEMA")

engine = insert_engine()
if not engine.dialect.has_schema(
    connection=engine.connect(),
    schema=db_schema,
    ):
    with engine.begin() as conn:
        conn.execute(CreateSchema(db_schema))
        conn.commit()

with engine.connect() as conn:
    Filings_Base.metadata.create_all(engine)
    conn.commit()
    conn.close()
engine.dispose()
