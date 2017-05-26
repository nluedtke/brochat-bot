FROM python:slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends python3-cryptography
    python3-pip && \
    pip install discord.py asyncio twython twilio && \
    apt-get remove -y python3-pip && \
    rm -rf /var/lib/apt/lists/*

COPY db.json gametime.py main.py tokens.config ./
ENTRYPOINT ["python3", "main.py"]

