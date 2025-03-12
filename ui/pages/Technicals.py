import streamlit as st
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))
from query_utils.technical_utils import technicals_ticker_stats
import pdb
import asyncio

# async def get_technicals():
    # Technicals Card
nTickers, nLatestTickers = asyncio.run(technicals_ticker_stats())

st.metric(label="Tickers\n(Technicals)", 
            value=f"{nTickers}", 
            delta=f"{nLatestTickers} in last day", 
            delta_color="normal", 
            help=None, 
            label_visibility="visible"
)

# if __name__ == "__main__":
#     asyncio.run(get_technicals())
