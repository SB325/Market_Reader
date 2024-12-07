FROM python:3.10-bullseye

USER root
WORKDIR /api

COPY requirements.txt .
RUN python -m pip install -r requirements.txt
COPY *.py .

ENTRYPOINT python api.py