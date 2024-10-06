'''
Class that manages all data transfers to and from the databases
'''
# from util.db.models.tickers import Symbols as SymbolTable
from util.db.conn import insert_engine
from util.logger import log
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import delete, select, text, bindparam
from sqlalchemy.orm import sessionmaker
import pdb
from io import StringIO
import pandas as pd
import time

engine = insert_engine()
Session = sessionmaker(bind=engine)
session = Session()

# TODO: Copies from first called file (facts, or submisions) succeed, but only first
#   copy from next file succeeds, rest fail. Fix this before proceeding.
class crud():
    conn = session.connection()

    def insert_rows(self, table, data: pd.DataFrame, add_index: bool = True) -> bool:
        status = False
        try:
            tablename = table.__tablename__
            columns = data.columns.tolist()
            sep = ','
            # save dataframe to an in memory buffer
            buffer = StringIO()

            data.to_csv(buffer, sep=sep, index=add_index, header=False)
            buffer.seek(0)

            cursor = self.conn.connection.cursor()
            try:
                # if tablename == 'business_addresses':
                #     pdb.set_trace()
                cursor.copy_from(buffer, tablename, sep=sep, null="")
                self.conn.commit()
            except (Exception) as error:
                print("Error: %s" % error)
                self.conn.rollback()
                cursor.close()
                return 1
            print("copy done.")
            cursor.close()

            status = True
        except Exception as exc:
            pdb.set_trace()
            log.error(f'Failure to insert data into DB.\n{exc}')
        
        return status

    def insert_rows_orm(self, table, index_elements: list, data: pd.DataFrame) -> bool:
        status = False
        pdb.set_trace()
        with self.conn as conn:
            conn.execute(insert(table).on_conflict_do_nothing(
                        index_elements=index_elements
                        ).values(data))
            conn.commit()
            status = True
        return status
    
    def query_table(self, table, column: str, query_val: str = ''):
        if query_val:
            stmt = select(table).where(column == query_val)
            result = self.conn.execute(stmt)
        else:
            stmt = select(getattr(table,column))
            result = self.conn.execute(stmt)
        out = result.all()
        if out:
            out = [n[0] for n in out]
        return out

    def delete_rows(self, column: str, table, query_val: str) -> bool:
        try:
            query = self.conn.query(table).filter(
                        table[column] == query_val
                        )
            if not query.first():
                log.warning(f'Deletion query returned 0 rows. Nothing to delete.')
                return False
            else:
                with self.conn as conn:
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