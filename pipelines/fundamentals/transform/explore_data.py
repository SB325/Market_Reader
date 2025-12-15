## Determine the set of filing types and their frequencies to determine the 
# name and number of milvus collections to create schemas for prior
# to data cleaning, parsing and vectorizing.

import pdb
import asyncio
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
from util.postgres.db.models.fundamentals import FundamentalsArtifacts as Fundamentals
from util.crud_pg import crud as crud
import pandas as pd

crud_util = crud()
columnName='primaryDocDescription'

async def main():
    pd.set_option('display.max_rows', 100)
    response = await crud_util.query_table(
                        tablename=Fundamentals, 
                        return_cols=[columnName], 
                        # unique_column_values=columnName,
                        )
    types = [val for val in response if val]

    df = pd.DataFrame(types, columns=['filing_type'])
    counts = df['filing_type'].value_counts()
    # counts.head(50)
    
    pdb.set_trace()

if __name__ == "__main__":
    asyncio.run(main())
