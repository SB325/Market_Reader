'''
Class that manages all data transfers to and from the databases
'''
from util.db.models.tickers import Symbols as SymbolTable
from util.db.conn import insert_engine
from util.logger import log
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import delete, select, text
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel
import pdb

Session = sessionmaker(bind=insert_engine())
session = Session()
engine = insert_engine()

class crud():

    def insert_rows(self, table, index_elements: list, data: list) -> bool:
        status = False
        try:
            with engine.connect() as conn:
                conn.execute(insert(table).on_conflict_do_nothing(
                            index_elements=index_elements
                            ), data)
                conn.commit()
            status = True
        except Exception as exc:
            log.error(f'Failure to insert data into DB.\n{exc}')
        
        return status

    def query_table(self, table, column: str, query_val: str = ''):
        if query_val:
            stmt = select(table).where(column == query_val)
            result = session.execute(stmt)
        else:
            stmt = select(getattr(table,column))
            result = session.execute(stmt)
        obj = result.all()
        if obj:
            out = [n[0] for n in obj]
        return out

    def delete_rows(column: str, table, query_val: str) -> bool:
        try:
            query = session.query(table).filter(
                        table[column] == query_val
                        )
            if not query.first():
                log.warning(f'Deletion query returned 0 rows. Nothing to delete.')
                return False
            else:
                with engine.connect() as conn:
                    conn.execute(
                        delete(table).where(
                        table[column] == query_val
                        )
                    )
                    conn.commit()
                    
            log.info(f'Successfully deleted {query_val}')

        except Exception as exc:
            log.error(f'Failure to perform delete operation.\n{exc}')
        
        return True