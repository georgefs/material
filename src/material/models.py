from django.db import models
from .hls import M3U8
from django.conf import settings

# Create your models here.


class Tag(models.Model):
    name = models.CharField(max_length=1024)

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.name


class Video(models.Model):
    name = models.CharField(max_length=1024)
    info = models.TextField()
    meta = models.TextField()
    preview_url = models.URLField(null=True)

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
        return M3U8.from_data(self.info)

    @property
    def default_folder(self):
        return "j1/material/{}__{}".format(self.id, self.name)

    def load_info(self, m3u8_url):
        m3u8 = M3U8.from_url(m3u8_url)
        self.info = m3u8.dump_data()


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
        return self.video.m3u8.slince(self.start, self.end)

    def preview_images(self):
        m3u8 = self.m3u8
        imgs = [v['file_path'] + ".jpg" for v in m3u8.scenes]
        return imgs
