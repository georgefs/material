import urllib.request
import tempfile
from django.conf import settings
from . import hls
import os
from . import gcs
from .models import Video
import urllib
import shutil


def download_mp4(url, target_path):
    urllib.request.urlretrieve(url, target_path)


def to_hls(source_path, target_path, preview):
    os.makedirs(target_path)
    hls.to_hls(source_path, target_path, preview)


def upload(path, gcs_path):
    bucket = settings.MATERIAL_BUCKET
    gcs.upload_folder(bucket, path, gcs_path)


def make_previews(path):
    hls.create_previews(path)


def create_video_from_url(name, url, video=None):
    if not video:
        video = Video.objects.create(name=name)
    tempfolder = tempfile.mktemp(dir=settings.MATERIAL_TMP)
    os.makedirs(tempfolder)

    target_path = os.path.join(tempfolder, 'video.mp4')
    target_hls_path = os.path.join(tempfolder, 'm3u8')
    m3u8_url = urllib.parse.urljoin(settings.MATERIAL_URL, os.path.join(video.default_folder, 'video.m3u8'))
    download_mp4(url, target_path)
    to_hls(target_path, target_hls_path, True)
    # make_previews(target_hls_path)
    upload(target_hls_path, video.default_folder)
    shutil.rmtree(tempfolder)
    video.load_info(m3u8_url)
    video.save()


def create_video_from_path(name, path, video=None):
    if not video:
        video = Video.objects.create(name=name)
    tempfolder = tempfile.mktemp(dir=settings.MATERIAL_TMP)
    os.makedirs(tempfolder)

    target_hls_path = os.path.join(tempfolder, 'm3u8')
    m3u8_url = urllib.parse.urljoin(settings.MATERIAL_URL, os.path.join(video.default_folder, 'video.m3u8'))
    to_hls(path, target_hls_path, True)
    # make_previews(target_hls_path)
    upload(target_hls_path, video.default_folder)
    shutil.rmtree(tempfolder)
    video.load_info(m3u8_url)
    video.save()
