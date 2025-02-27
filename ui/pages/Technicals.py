import streamlit as st
from streamlit_echarts import st_echarts
# https://github.com/andfanilo/streamlit-echarts/tree/develop/img
# https://github.com/arnaudmiribel/streamlit-extras?tab=readme-ov-file
# https://medium.com/nerd-for-tech/build-your-first-candlestick-chart-with-streamlit-7edd31ae559d

options = {
    "xAxis": {
        "type": "category",
        "data": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    },
    "yAxis": {"type": "value"},
    "series": [
        {"data": [820, 932, 901, 934, 1290, 1330, 1320], "type": "line"}
    ],
}
st_echarts(options=options)