'''
Class that manages all data transfers to and from the databases
'''
import asyncio
from util.postgres.db.conn import insert_engine
from util.logger import log
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import delete, select, column, table
import pdb
from io import StringIO
import pandas as pd
import time
from typing import Union
from enum import Enum

class operationType(Enum):
    gt = 'gt'
    lt = 'lt'
    eq = 'eq'

    def __str__(self):
        return str.__str__(self.value)
    
# TODO: Copies from first called file (facts, or submisions) succeed, but only first
#   copy from next file succeeds, rest fail. Fix this before proceeding.
class crud():
    engine = insert_engine()

    async def insert_rows(self, table, data: pd.DataFrame, add_index: bool = True) -> bool:
        status = False
        try:
            tablename = table.__tablename__
            columns = data.columns.tolist()
            sep = ','
            # save dataframe to an in memory buffer
            buffer = StringIO()

            data.to_csv(buffer, sep=sep, index=add_index, header=False)
            buffer.seek(0)

            conn =  self.engine.raw_connection()
            cursor = conn.cursor()
            try:
                cursor.copy_from(buffer, tablename, sep=sep, null="")
                conn.commit()
            except (Exception) as error:
                print("Error: %s" % error)
                conn.rollback()
                cursor.close()
                return 1
            print("copy done.")
            cursor.close()
            conn.close()
            
            status = True
        except Exception as exc:
            pdb.set_trace()
            log.error(f'Failure to insert data into DB.\n{exc}')
        
        return status
    
    async def query_table(self, tablename:str, cols: Union[str, list], query_val: str = '', query_operation: operationType = 'eq'):
        with self.engine.connect() as conn:
            if query_val:
                if 'eq' in query_operation:
                    stmt = select(table(tablename)).where(column(cols) == query_val)
                if 'gt' in query_operation:
                    stmt = select(table(tablename)).where(column(cols) > query_val)
                if 'lt' in query_operation:
                    stmt = select(table(tablename)).where(column(cols) < query_val)
                out = conn.execute(stmt).all()
            else:
                if isinstance(cols, list):
                    cols_ = [column(col) for col in cols]
                    stmt = select(table(tablename.__tablename__, *cols_))
                    result = conn.execute(stmt)
                    out = result.all()
                else:
                    stmt = select(table(tablename), column(cols))
                    result = conn.execute(stmt)
                    out = result.all()
                    if out:
                        out = [n[0] for n in out]
            
        return out

    async def delete_rows(self, column: str, tablename, query_val: str) -> bool:
        try:
            with self.engine.connect() as conn:
                query = conn.query(tablename.filter(
                            tablename[column] == query_val
                            ))
                if not query.first():
                    log.warning(f'Deletion query returned 0 rows. Nothing to delete.')
                    return False
                else:
                    with conn as conn:
                        conn.execute(
                            delete(tablename).where(
                            tablename[column] == query_val
                            )
                        )
                        conn.commit()
                    
            log.info(f'Successfully deleted {query_val}')

        except Exception as exc:
            log.error(f'Failure to perform delete operation.\n{exc}')
        
        return True
    
    async def insert_rows_orm(self, tablename, index_elements: list, data: Union[list, pd.DataFrame]) -> bool:
        status = False
        # pdb.set_trace()
        if isinstance(data, pd.DataFrame):
            with self.engine.connect() as conn:
                conn.execute(insert(table(tablename)).on_conflict_do_nothing(
                            index_elements=index_elements
                            ).values(data))
                conn.commit()
                status = True
        else:
            with self.engine.connect() as conn:
                conn.execute(insert(table(tablename)).on_conflict_do_nothing(
                            index_elements=index_elements
                            ), data)
                conn.commit()
                status = True
        return status
    