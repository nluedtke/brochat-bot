FROM python:slim
RUN apt-get update
RUN apt-get install -y --no-install-recommends python-cryptography python-pip
RUN pip install discord.py asyncio twython twilio
COPY . .
CMD ["python", "main.py"]
