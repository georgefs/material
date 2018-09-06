from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Video, VideoScene
from django.urls import reverse
from django.utils.html import format_html
from datetime import timedelta
import json


class VideoAdmin(admin.ModelAdmin):
    class Media:
        js = ('js/admin/mymodel.js',)

    list_display = ('video_name', 'm3u8_url', 'preview', 'scenes', 'streaming_url')

    def m3u8_url(self, obj):
        url = reverse('video_m3u8', kwargs={'vid': obj.id})
        return format_html("<a Target='_new' href='{}'>{}</a>".format(url, 'm3u8_url'))

    def preview(self, obj):
        url = reverse('video_preview', kwargs={'vid': obj.id})
        return format_html("<a Target='_new' href='{}'>{}</a>".format(url, 'preview'))

    def scenes(self, obj):
        url = reverse('admin:material_videoscene_changelist')
        url += "?video__name={}".format(obj.name)
        return format_html("<a Target='_self' href='{}'>{}</a>".format(url, 'scenes'))

    def video_name(self, obj):
        meta = json.loads(obj.meta.strip() or '{}')
        if meta.get('type', '' ) == 'J1':
            return "{type}-{section} {left} {left_score}:{right_score} {right}".format(**meta)
        else:
            return obj.name

    def streaming_url(self, obj):
        url = reverse('video_streaming_m3u8', kwargs={'vid': obj.id})
        query = "?start_time=2018-09-01T00:00:00&cycle_seconds=7200"
        url += query
        return format_html("<a Target='_self' href='{}'>{}</a>".format(url, 'streaming_url'))


class VideoSceneAdmin(admin.ModelAdmin):
    class Media:
        js = ('https://cdn.jsdelivr.net/npm/clappr@latest/dist/clappr.min.js',)

    list_display = ('id', 'tag_names', 'text', 'video__name', 'm3u8_url', 'preview', 'mp4')

    list_filter = ('tags', 'video__name')

    def m3u8_url(self, obj):
        url = reverse('scene_m3u8', kwargs={'vid': obj.id})
        return format_html("<a Target='_new' href='{}'>{}</a>".format(url, 'm3u8_url'))

    def preview(self, obj):
        url = reverse('scene_preview_images', kwargs={'vid': obj.id})
        return format_html("<a Target='_new' href='{}'>{}</a>".format(url, 'preview'))

    def video__name(self, obj):
        meta = json.loads(obj.video.meta)
        return "{left} {left_score}:{right_score} {right}".format(**meta)

    def mp4(self, obj):
        url = "http://35.229.199.4/{}.mp4".format(obj.id)
        return format_html("<a Target='_new' href='{}'>{}</a>".format(url, 'mp4'))

    def duration(self, obj):
        st = obj.start
        ed = obj.end
        st = timedelta(int(st))
        ed = timedelta((ed))
        duration = "{} to {}".format(st, ed)
        return duration

    def tag_names(self, obj):
        return "\n".join(["【{}】".format(o.name) for o in obj.tags.all()])

admin.site.register(Video, VideoAdmin)
admin.site.register(VideoScene, VideoSceneAdmin)
