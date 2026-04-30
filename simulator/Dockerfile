FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir -e .

ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO
ENV MQTT_BROKER=mosquitto
ENV MQTT_PORT=1883
ENV INITIAL_SCENARIO=normal

ENTRYPOINT ["python", "-m", "evenkeel_sim"]
