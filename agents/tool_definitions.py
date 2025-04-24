import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))
from pipelines.press_releases.newswires import newswire
from util.crud_pg import crud
from util.elastic.crud_elastic import crud_elastic
from util.requests_util import requests_util
from util.time_utils import to_posix
from util.postgres.db.models.tickers import Technicals as Technicals
from util.postgres.db.models.tickers import Filings as Filings
from util.postgres.db.models.tickers import Symbols as Symbols
from util.postgres.db.models.tickers import Company_Meta as Company
from util.postgres.db.models.tickers import Company_Business_Addresses as Address
import asyncio
from tool_schemas import news_article_model, technical_model, fundamentals_model
import pdb

requests = requests_util()
# Databases
celastic = crud_elastic()
nw = newswire(celastic) 
crudpg = crud()

async def get_company_names():
    try:
        name_dict = await crudpg.query_table(
            Symbols,
            return_cols = ['title', 'cik_str'],
            unique_column_values='cik_str',
            )
    except BaseException as Err:
        print(f'Error: {Err}')
        pdb.set_trace()
    return name_dict

def get_news_articles(ticker, since_date):
    # since_date is a YYYY/MM/DD string
    try:
        query_on_val = str(to_posix(since_date, "%Y-%m-%d"))
        articles = nw.search_ticker(
                    index = 'market_news', 
                    ticker = ticker,
                    conditional ='gte',
                    query_on_key = 'created',
                    query_on_val = query_on_val
                    )
    except BaseException as Err:
        print(f'Error: {Err}')
        pdb.set_trace()
    return articles

async def get_technical_info(ticker, since_date):
    # since_date is a DD/MM/YYYY string
    try:
        since_date_posix = str(to_posix(since_date, "%Y-%m-%d"))
        tech_response = await crudpg.query_table(
                Technicals,
                query_col=['ticker','datetime'], 
                query_val=[ticker, since_date_posix], 
                query_operation=['eq', 'gt'],
                sort_column='datetime'
                )
    except BaseException as Err:
        print(f'Error: {Err}')
        pdb.set_trace()

    return tech_response

async def get_company_meta(cik):
    try:
        company_meta = await crudpg.query_table(
            Company,
            return_cols = ['name', 
                           'tickers', 
                           'cik', 
                           'exchanges', 
                           'sicDescription',
                           'ownerOrg',
                           'formerNames'],
            query_col='cik', 
            query_val=cik,
            unique_column_values='cik'
            )
    except BaseException as Err:
        print(f'Error: {Err}')
        pdb.set_trace()
    return company_meta

async def get_business_address(cik):
    try:
        tech_response = await crudpg.query_table(
                Address,
                return_cols=['cik',
                             'street1',
                             'street2',
                             'city',
                             'stateOrCountry',
                             'stateOrCountryDescription',
                             'cik'],
                query_col='cik', 
                query_val=cik, 
                unique_column_values='cik',
                )
    except BaseException as Err:
        print(f'Error: {Err}')
        pdb.set_trace()
    return tech_response

def make_links(set_):
    return f"https://www.sec.gov/Archives/edgar/data/{set_[0]}/{set_[1].replace('-','')}/{set_[2]}"

async def get_filing_info(cik, since_date):
    # https://www.sec.gov/Archives/edgar/data/320193/000032019325000008/aapl-20241228.htm
    # https://www.sec.gov/Archives/edgar/data/f{cik}/f{accessionNumber}/f{primaryDocument}
    since_date_posix = str(to_posix(since_date, "%Y-%m-%d"))
    filing_response = await crudpg.query_table(
            Filings,
            return_cols = ['cik', 'accessionNumber', 'primaryDocument'],
            query_col=['cik', 'filingDate'], 
            query_val=[cik, since_date_posix], 
            query_operation=['eq', 'gt'],
            sort_column='filingDate'
            )
    links = [make_links(val) for val in filing_response]
    return links

if __name__ == "__main__":
    company_dict = asyncio.run(get_company_names())
    company_name = 'Apple'
    since_date = '2025-02-01'

    ticker = [val for val in company_dict if company_name in val[0]]
    if not ticker:
        print(f'Company Name -{company_name}- Not Found!')
    else:    
        ciks = [tick[1] for tick in ticker]
        company_meta = [asyncio.run(get_company_meta(res)) for res in ciks]
        resolved_tickers = [ ''.join([(vv) for vv in val[0][1] if vv.isalpha()]) for val in company_meta ]
        addresses = [asyncio.run(get_business_address(res)) for res in ciks]
        news_articles = [get_news_articles(tick, since_date) for tick in resolved_tickers]
        technical_data = [asyncio.run(get_technical_info(tick, since_date)) for tick in resolved_tickers]
        filing_data = [asyncio.run(get_filing_info(cik, since_date)) for cik in ciks]
