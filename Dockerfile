FROM python:3.12-slim
LABEL authors="diogobaeder"

RUN mkdir "/app"
WORKDIR /app
COPY requirements.in /app/
RUN pip install -r requirements.in
COPY . /app/

ENTRYPOINT /app/start-app.sh
