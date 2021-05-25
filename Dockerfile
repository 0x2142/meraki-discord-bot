FROM python:3.8.0-slim
COPY . /app

WORKDIR app
RUN pip install -r requirements.txt
ENTRYPOINT uvicorn meraki-discord-bot:app --reload --host 0.0.0.0 --port 8080
EXPOSE 8080
