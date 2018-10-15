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
        return M3U8.from_data(self.info)

    @property
    def default_folder(self):
        return "j1/material/{}__{}".format(self.id, self.name)

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


