import os
import logging
import redis
from minio import Minio
from demucs.pretrained import get_model
import torchaudio
import torch
from demucs.apply import apply_model

logging.basicConfig(level=logging.DEBUG)

# Environment Variables
redis_host = os.getenv('REDIS_HOST', 'redis')
minio_host = os.getenv('MINIO_HOST', 'minio') + ":9000"
minio_access_key = os.getenv('MINIO_ACCESS_KEY', 'rootuser')
minio_secret_key = os.getenv('MINIO_SECRET_KEY', 'rootpass123')

r = redis.StrictRedis(host=redis_host, port=6379, db=0, decode_responses=True)

minio_client = Minio(
    minio_host,
    access_key=minio_access_key,
    secret_key=minio_secret_key,
    secure=False
)

queue_name = 'toWorkers'

logging.info("Loading Demucs model...")
device = 'cuda' if torch.cuda.is_available() else 'cpu'
model = get_model('htdemucs')
model.to(device).eval()
logging.info("Demucs model loaded successfully.")

torchaudio.set_audio_backend("sox_io")

def process_message(message):
    try:
        mp3_file_path = f"/tmp/{message}.mp3"
        output_dir = f"/tmp/output/{message}"
        os.makedirs(output_dir, exist_ok=True)

        minio_client.fget_object("input-tracks", f"{message}.mp3", mp3_file_path)

        wav, sr = torchaudio.load(mp3_file_path)
        wav = wav.to(device)

        if wav.dim() == 1:
            wav = wav.unsqueeze(0)
        if wav.dim() == 2:
            wav = wav.unsqueeze(0)

        sources = apply_model(model, wav, shifts=0, split=True)
        sources = sources.squeeze(0)

        parts = ["vocals", "drums", "bass", "other"]
        for i, part in enumerate(parts):
            output_file = f"{output_dir}/{message}-{part}.mp3"
            source_audio = sources[i]
            torchaudio.save(output_file, source_audio.cpu(), sr)
            minio_client.fput_object("output-tracks", f"{message}-{part}.mp3", output_file)

        os.remove(mp3_file_path)
        logging.info(f"Processed message: {message}")

    except Exception as e:
        logging.error(f"Error processing message: {e}")

if __name__ == "__main__":
    logging.info("Starting worker server...")
    while True:
        message = r.lpop(queue_name)

        if message:
            try:
                process_message(message)
            except Exception as e:
                logging.error(f"Error processing message: {e}")