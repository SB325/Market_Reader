FROM python:3.10-bullseye

USER root
WORKDIR /api

COPY *.py .
COPY requirements.txt .

RUN python -m pip install -r requirements.txt

ENTRYPOINT python api.py