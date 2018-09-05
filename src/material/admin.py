from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Video, VideoScene
from django.urls import reverse
from django.utils.html import format_html
import json

class VideoAdmin(admin.ModelAdmin):
    class Media:
        js = ('js/admin/mymodel.js',)

    list_display = ( 'name', 'm3u8_url', 'preview', 'scenes' )

    def m3u8_url(self, obj):
        url = reverse('video_m3u8', kwargs={'vid':obj.id})
        return format_html("<a Target='_new' href='{}'>{}</a>".format(url, 'm3u8_url'))

    def preview(self, obj):
        url =  reverse('video_preview', kwargs={'vid':obj.id})
        return format_html("<a Target='_new' href='{}'>{}</a>".format(url, 'preview'))

    def scenes(self, obj):
        url = reverse('admin:material_videoscene_changelist')
        url += "?video__name={}".format(obj.name)
        return format_html("<a Target='_self' href='{}'>{}</a>".format(url, 'scenes'))


class VideoSceneAdmin(admin.ModelAdmin):
    class Media:
        js = ('https://cdn.jsdelivr.net/npm/clappr@latest/dist/clappr.min.js',)

    list_display = ( 'id', 'tag_names', 'text', 'video__name', 'm3u8_url', 'duration', 'preview', 'mp4')
    list_filter = ('video__name', )
    def m3u8_url(self, obj):
        url =  reverse('scene_m3u8', kwargs={'vid':obj.id})
        return format_html("<a Target='_new' href='{}'>{}</a>".format(url, 'm3u8_url'))

    def preview(self, obj):
        url =  reverse('scene_preview_images', kwargs={'vid':obj.id})
        return format_html("<a Target='_new' href='{}'>{}</a>".format(url, 'preview'))

    def video__name(self, obj):
        meta = json.loads(obj.video.meta)
        return "{left} {left_score}:{right_score} {right}".format(**meta)
        return obj.video.name

    def mp4(self, obj):
        url = "http://130.211.252.81/{}.mp4".format(obj.id)
        return format_html("<a Target='_new' href='{}'>{}</a>".format(url, 'mp4'))

    def duration(self, obj):
        st = obj.start
        ed = obj.end
        duration = "{}:{}:{} to {}:{}:{}".format(int(st/3600), int(st%3600/60), st%60, int(ed/3600), int(ed%3600/60), ed%60)
        return duration

    def tag_names(self, obj):
        return "\n".join(["【{}】".format(o.name) for o in obj.tags.all()])



admin.site.register(Video, VideoAdmin)
admin.site.register(VideoScene, VideoSceneAdmin)
