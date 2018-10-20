from django.db import models
from .hls import M3U8
from . import hls
#from django.conf.settings import MATERIAL_URL, MATERIAL_VIDEO_PATH
from django.conf import settings
import os
import json, requests, re
from . import highlight
import tempfile
import io
import subprocess

# Create your models here.


class Tag(models.Model):
    name = models.CharField(max_length=1024)

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.name


class Video(models.Model):
    live = models.BooleanField(default=False)

    name = models.CharField(max_length=1024)
    info = models.TextField()
    meta = models.TextField()
    preview_url = models.URLField(null=True, blank=True)

    class Meta:
        verbose_name = '影片'
        verbose_name_plural = '影片'


    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.name

    @staticmethod
    def sync(name, m3u8_url):
        m3u8 = M3U8.from_url(m3u8_url)
        return Video.objects.create(name=name, info=m3u8.dump_data())

    @property
    def m3u8(self):
        if self.live:
            print(self.direct_url)
            return M3U8.from_url(self.direct_url)
        else:
            return M3U8.from_data(self.info)

    @property
    def default_folder(self):
        return "j1/material/{}".format(self.id, self.name)
    
    @property
    def abspath(self):
        return os.path.join(settings.MATERIAL_VIDEO_PATH, self.default_folder)

    @property
    def direct_url(self):
        return settings.MATERIAL_URL + "{}/video.m3u8".format(self.default_folder)

    def load_info(self, m3u8_url):
        m3u8 = M3U8.from_url(m3u8_url)
        self.info = m3u8.dump_data()

    def slice(self, text, start, end, meta={}, tags=[]):
        scene = VideoScene.objects.create(
            video=self,
            text=text,
            start=start,
            end=end,
            meta=meta
        )
        for tag in tags:
            scene.tags
            scene.add(tag)
        return scene

class Streaming(models.Model):
    STATUS_CHOICES = (
        ('init', 'init'),
        ('wait', 'wait'),
        ('live', 'live'),
        ('done', 'done'),
        ('fails', 'fails'),
    )
    name = models.CharField(max_length=1024)
    status = models.CharField(max_length=1024, choices=STATUS_CHOICES, default='wait')
    start = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    duration = models.DurationField(default=0)
    video = models.ForeignKey(Video, on_delete=models.CASCADE, null=True, blank=True)
    url = models.URLField()

    def save(self, *args, **kwargs):
        if not self.pk:
            self.video = Video.objects.create(name="{}_{}".format(self.pk, self.name), live=True)
        super(Streaming, self).save(*args, **kwargs)

    def start_live(self, copycodec=False, delay=False):
        self.status = 'live'
        return hls.to_hls(self.url, self.video.abspath, True, copycodec, delay)



class VideoScene(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    text = models.CharField(max_length=1024)
    start = models.IntegerField()
    end = models.IntegerField()
    preview_url = models.URLField(null=True)
    tags = models.ManyToManyField(Tag)
    meta = models.TextField()

    def __unicode__(self):
        return self.text

    def __str__(self):
        return self.text

    @property
    def m3u8(self):
        return self.video.m3u8.slice(self.start, self.end)

    def preview_images(self):
        m3u8 = self.m3u8
        imgs = [v['file_path'] + ".jpg" for v in m3u8.scenes]
        return imgs

    class Meta:
        verbose_name = '精彩片段'
        verbose_name_plural = '精彩片段'



class Collection(models.Model):
    #synced = models.BooleanField(default=False)
    name = models.CharField(max_length=2048)
    text = models.TextField(blank=True)
    scenes = models.TextField()
    meta = models.TextField(default='{}')

    @property
    def m3u8(self):
        vids = self.scenes.split(',')
        print(vids)
        vids = [int(v) for v in vids]
        info = dict([(v.id, v.m3u8) for v in VideoScene.objects.filter(id__in=vids)])
        m3u8 = M3U8.concat([info[vid] for vid in vids])
        print(m3u8)
        return m3u8

    class Meta:
        verbose_name = '精彩錦集'
        verbose_name_plural = '精彩錦集'

    def sync(self):
        scenes = self.m3u8.scenes
        vs = [v['file_path'] for v in scenes]
        source = "|".join(vs)
        tempfolder = tempfile.mkdtemp()
        output_path = os.path.join(tempfolder, "video.mp4")

        cmd = 'ffmpeg -protocol_whitelist concat,file,http,https,tcp,tls -i concat:{source} -vcodec copy -acodec copy {output_path}'.format(source=source, output_path=output_path).split()

        proc = subprocess.Popen(cmd)
        proc.wait()

        img = scenes[0]['file_path']+".jpg"
        img_content = requests.get(img).content
        img_temp = os.path.join(tempfolder, "video.jpg")
        with open(img_temp, 'wb+') as f:
            f.write(img_content)
        
        data = {}
        data['name'] = self.name
        data['tags'] = " ".join(json.loads(self.meta))
        data['description'] = self.text
        data['league'] = 111
        data['cover_image'] = open(img_temp, 'rb')
        data['file'] = open(output_path, 'rb')

        highlight.upload(data)
        self.sync=True
        self.save()
