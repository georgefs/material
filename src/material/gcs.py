from google.cloud import storage
import os
client = storage.Client()


def upload_path(bucket, path, target_path):
    bucket = client.bucket(bucket)
    target = bucket.blob(target_path)
    target.upload_from_filename(path)


def upload_folder(bucket, path, target_path):
        bucket = client.bucket(bucket)
        for root, dirs, fs in os.walk(path):
            for f in fs:
                source = os.path.join(root, f)
                base_path = os.path.relpath(root, path)
                target = os.path.join(target_path, os.path.join(base_path, f)).replace('./', '')
                target = bucket.blob(target)
                target.upload_from_filename(source)
