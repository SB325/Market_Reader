import streamlit as st
from query_utils.technical_utils import technicals_ticker_stats, fundamentals_ticker_stats, news_ticker_stats
import asyncio

async def get_stats():
    col0, col1, col2 = st.columns(3)
    # # Technicals Card
    # nTickers, nLatestTickers = await technicals_ticker_stats()
    # col0.metric("Tickers\n(Technicals)", 
    #             f"{nTickers}", 
    #             delta=f"{nLatestTickers} in last day", 
    #             delta_color="normal", 
    #             help=None, 
    #             label_visibility="visible"
    # )

    # # Fundamentals Card
    # nTickers, nLatestTickers = await fundamentals_ticker_stats()
    # col1.metric("Tickers\n(Fundamentals)", 
    #             f"{nTickers}", 
    #             delta=f"{nLatestTickers} in last day", 
    #             delta_color="normal", 
    #             help=None, 
    #             label_visibility="visible"
    # )

    # News Card
    ndocs = await news_ticker_stats()
    ndocs_label = ndocs
    if ndocs > 1_000_000:
        ndocs_label = "{:.1f}M".format(ndocs/1_000_000)
    elif ndocs > 1_000:
        ndocs_label = "{:.1f}K".format(ndocs/1_000)
        
    col2.metric("Documents\n(News)",
                f"{ndocs_label}", 
                label_visibility="visible")
        
if __name__ == "__main__":
    asyncio.run(get_stats())
    
    