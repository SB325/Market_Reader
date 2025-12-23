## Determine the set of filing types and their frequencies to determine the 
# name and number of milvus collections to create schemas for prior
# to data cleaning, parsing and vectorizing.

import pdb
import asyncio
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.append(os.path.join(os.getcwd()))
from util.postgres.db.models.fundamentals import FundamentalsArtifacts as Fundamentals
from util.crud_pg import crud as crud
import pandas as pd
from pipelines.fundamentals.transform.clean_html import clean_html

crud_util = crud()
columnName='primaryDocDescription'

target_filings = ['10-Q', '10-K', '8-K', '6-K', 'FORM 4',
                'DEF 14A', 'FORM 3', 'S-4', 'S-8', 
                '40F', '424A', '424B', 'SC 13DA', 
                '20-F', '10-QA', '11-K', 'SCHEDULE 13G']

async def print_unique_filing_types(filing_df):
    pd.set_option('display.max_rows', 100)
    types = await crud_util.query_table(
                        tablename=Fundamentals, 
                        return_cols=[columnName], 
                        )
                        
    df = pd.DataFrame(types, columns=['filing_type'])

    counts = df['filing_type'].value_counts()
    print(counts.head(50))

async def get_content_from_filing_type(type_str, limit_n):
    content_list = await crud_util.query_table(
                        tablename=Fundamentals, 
                        query_col=columnName,
                        query_val=type_str,
                        return_cols=['content'],
                        limit=limit_n,
                        )
    pdb.set_trace()
    return content_list

async def main():
    # print_unique_filing_types(df):

    content_list = await get_content_from_filing_type('10-Q', 1)
    pdb.set_trace()
    clean_html()
    

if __name__ == "__main__":
    asyncio.run(main())

## Common Filing types and Descriptions:
# 10-Q - The 10-Q provides investors regular check-ins to a company’s health from quarter to quarter.
# 10-K - The annual report on Form 10-K provides a comprehensive overview of the company’s business and financial condition and includes audited financial statements.
# 8-K - The Form 8-K reports major events that shareholders should know about.
# 4 - The Form 4 reports changes in ownership by insiders and must be reported to the SEC within two business days.
# 6-K - Current report of foreign issuer pursuant to Rules 13a-16 and 15d-16 Amendments

## Less Commmon Filing types and Descriptions:
# DEF 14A - Definitive proxy statement. Required ahead of annual meeting when firm is soliciting shareholder votes.
# 3 - Initial statement of beneficial ownership of securities
# S-4 - Registration of securities issued in business combination transactions
# S-4 POS - Post-effective amendment to a S-4EF registration statemen
# S-8 - Initial registration statement for securities to be offered to employees pursuant to employee benefit plans
# 40F - Annual reports filed by certain Canadian issuers pursuant to Section 15(d) and Rule 15d-4
# 424A* - Prospectus filed pursuant to Rule 424(a)
# 424B* - Prospectus filed pursuant to Rule 424(b)*
# SC 13DA - beneficial ownership report that must be filed by anyone who acquires more than 5% of a class of a public company's voting securities with the intent to influence control of the company. 
# 20-F - disclosure document filed with the U.S. Securities and Exchange Commission (SEC) by foreign private issuers that have listed their equity shares on U.S. stock exchanges
# 10-QA - used to correct or update information in a previously filed quarterly report (Form 10-Q) 
# 11-k - annual report that public companies must file with the Securities and Exchange Commission (SEC) for employee stock purchase, savings, and similar plans.
target_filings = ['10-Q', '10-K', '8-K', '6-K', 'FORM 4',
                'DEF 14A', 'FORM 3', 'S-4', 'S-8', 
                '40F', '424A', '424B', 'SC 13DA', 
                '20-F', '10-QA', '11-K']