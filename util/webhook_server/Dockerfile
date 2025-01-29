FROM python:3.10-bullseye

USER root
WORKDIR /webhook

COPY requirements.txt .
RUN pip install --upgrade pip setuptools==57.5.0 
RUN python -m pip install -r requirements.txt
COPY *.py .
COPY *.env .

ENTRYPOINT python webhook_server.py