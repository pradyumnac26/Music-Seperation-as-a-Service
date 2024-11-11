from flask import Flask, request, jsonify, send_file
import base64
import redis
import uuid
import os
from minio import Minio
from minio.error import S3Error

app = Flask(__name__)

r = redis.Redis(host='redis', port=6379, db=0)

minio_client = Minio(
    "minio-proj.minio-ns.svc.cluster.local:9000",  # MinIO service URL
    access_key="rootuser",
    secret_key="rootpass123",
    secure=False
)


input_bucket = "input-tracks"
output_bucket = "output-tracks"

if not minio_client.bucket_exists(input_bucket):
    minio_client.make_bucket(input_bucket)
if not minio_client.bucket_exists(output_bucket):
    minio_client.make_bucket(output_bucket)

@app.route('/apiv1/separate', methods=['POST'])
def separate():
    data = request.json
    mp3_data = base64.b64decode(data['mp3'])
    songhash = str(uuid.uuid4())
    
    object_name = f"{songhash}.mp3"

    try:
        temp_file_path = f"/tmp/{object_name}"
        with open(temp_file_path, "wb") as f:
            f.write(mp3_data)

        minio_client.fput_object(input_bucket, object_name, temp_file_path)
        os.remove(temp_file_path)
        r.lpush('toWorkers', songhash)
        callback_url = data.get('callback')
        if callback_url:
            pass

        return jsonify({'songhash': songhash, 'message': 'File uploaded to MinIO and task queued for processing'}), 200

    except S3Error as e:
        return jsonify({'error': f"MinIO error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/apiv1/track/<track>', methods=['GET'])
def get_track(track):
    track_path = f"/tmp/{track}.mp3"
    try:
        minio_client.fget_object(output_bucket, f"{track}.mp3", track_path)
        return send_file(track_path, as_attachment=True)

    except S3Error as e:
        return jsonify({'error': f"MinIO error: {str(e)}"}), 500
    except FileNotFoundError:
        return "Track not found", 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if os.path.exists(track_path):
            os.remove(track_path)


@app.route('/apiv1/remove/<track>', methods=['DELETE'])
def remove_track(track):
    try:
        minio_client.remove_object(output_bucket, f"{track}.mp3")
        return "Track removed from MinIO storage", 200

    except S3Error as e:
        return jsonify({'error': f"MinIO error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/apiv1/queue', methods=['GET'])
def get_queue():
    try:
        queue = r.lrange('toWorkers', 0, -1)
        return jsonify([q.decode('utf-8') for q in queue]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/apiv1/bucket', methods=['GET'])
def get_bucket_content():
    try:
        buckets = minio_client.list_buckets()
        bucket_content = {}
        for bucket in buckets:
            objects = minio_client.list_objects(bucket.name, recursive=True)
            bucket_content[bucket.name] = [obj.object_name for obj in objects]
        return jsonify(bucket_content), 200
    except S3Error as e:
        return jsonify({'error': f"MinIO error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/apiv1/delete_contents', methods=['GET'])
def delete_bucket_content():
    try:
        buckets = minio_client.list_buckets()
        for bucket in buckets:
            objects = minio_client.list_objects(bucket.name, recursive=True)
            for obj in objects:
                minio_client.remove_object(bucket.name, obj.object_name)
        return "All objects deleted", 200
    except S3Error as e:
        return jsonify({'error': f"MinIO error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
