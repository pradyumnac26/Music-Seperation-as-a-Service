FROM python:3.9-slim

RUN apt-get update && apt-get install -y ffmpeg

RUN pip3 install demucs torchaudio redis minio requests

WORKDIR /app

COPY worker-server.py .

RUN chmod +x worker-server.py

RUN python3 -m demucs.separate --help

CMD ["python3", "worker-server.py"]
