FROM python:3.11-slim

WORKDIR /app

# copy repository into container
COPY . /app

# install Python deps
RUN pip install --no-cache-dir -r requirements.txt

# sensible default inside container
ENV DUMP_DIR=/app/Dump

RUN mkdir -p /app/Dump/processed /app/logs

CMD ["python", "main.py"]
