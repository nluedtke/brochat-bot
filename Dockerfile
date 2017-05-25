FROM python:slim
RUN apt-get update && \
    apt-get install -y --no-install-recommends python-cryptography python-pip && \
    pip install discord.py asyncio twython twilio && \
    apt-get remove -y python-pip && \
    rm -rf /var/lib/apt/lists/*

COPY db.json .
COPY gametime.py .
COPY main.py .
COPY tokens.config .
ENTRYPOINT ["python3", "main.py"]

