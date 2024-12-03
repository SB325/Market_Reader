FROM python:3.10-bullseye

USER root
WORKDIR /api
COPY ./pipelines/fundamentals/vectorize/*.py .
COPY ./requirements.txt .

ENTRYPOINT "python api.py"