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

    list_display = ('video_name', 'slince', 'links', 'scenes')

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

    def slince(self, obj):
        url = reverse('video_slince', kwargs={'vid': obj.id})
        return format_html("<a Target='_new' href='{}'>{}</a>".format(url, 'slince'))


    def links(self, obj):
        html = ""
        url = reverse('video_m3u8', kwargs={'vid': obj.id})
        html += "<a Target='_new' href='{}'>{}</a><br/>".format(url, 'm3u8_url')
        url = reverse('video_preview', kwargs={'vid': obj.id})
        html += "<a Target='_new' href='{}'>{}</a><br/>".format(url, 'preview')
        url = reverse('video_streaming_m3u8', kwargs={'vid': obj.id})
        query = "?start_time=2018-09-01T00:00:00&cycle_seconds=7200"
        url += query
        html += "<a Target='_new' href='{}'>{}</a>".format(url, 'streaming_url')
        return format_html(html)



class VideoSceneAdmin(admin.ModelAdmin):
    class Media:
        js = ('https://cdn.jsdelivr.net/npm/clappr@latest/dist/clappr.min.js',)

    list_display = ('id', 'tag_names', 'text', 'video__name', 'links', 'edit', 'mp4')

    list_filter = ('tags', 'video__name')


    def edit(self, obj):
        url = reverse('scene_edit', kwargs={'vid': obj.id})
        return format_html("<a Target='_new' href='{}'>{}</a>".format(url, 'edit'))

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

    def links(self, obj):
        html = ""
        url = reverse('scene_m3u8', kwargs={'vid': obj.id})
        html += "<a Target='_new' href='{}'>{}</a><br/>".format(url, 'm3u8_url')
        url = reverse('scene_preview', kwargs={'vid': obj.id})
        html += "<a Target='_new' href='{}'>{}</a>".format(url, 'preview')
        return format_html(html)


admin.site.register(Video, VideoAdmin)
admin.site.register(VideoScene, VideoSceneAdmin)
