from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Video, VideoScene, Collection
from django.urls import reverse
from django.utils.html import format_html
from datetime import timedelta
import json


class VideoAdmin(admin.ModelAdmin):
    class Media:
        js = ('js/admin/mymodel.js',)

    list_display = ('video_name', 'slice', 'links', 'scenes')
    list_filter = ('id', )

    def scenes(self, obj):
        url = reverse('admin:material_videoscene_changelist')
        url += "?q={}".format(obj.name)
        return format_html("<a Target='_self' href='{}'>{}</a>".format(url, 'scenes'))

    def video_name(self, obj):
        meta = json.loads(obj.meta.strip() or '{}')
        if meta.get('type', '' ) == 'J1':
            return "{type}-{section} {left} {left_score}:{right_score} {right}".format(**meta)
        else:
            return obj.name

    def slice(self, obj):
        url = reverse('video_slice', kwargs={'vid': obj.id})
        return format_html("<a Target='_new' href='{}'>{}</a>".format(url, 'slice'))


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

    list_display = ('id', 'tag_names', 'text', 'video__name', 'links', 'edit', 'mp4', 'start')

    list_filter = ('tags', )
    search_fields = ('text', 'video__name' )


    def edit(self, obj):
        url = reverse('scene_edit', kwargs={'vid': obj.id})
        return format_html("<a Target='_new' href='{}'>{}</a>".format(url, 'edit'))

    def video__name(self, obj):
        try:
            meta = json.loads(obj.video.meta)
            text = "{left} {left_score}:{right_score} {right}".format(**meta)
        except:
            text = obj.video.name

        url = reverse('admin:material_video_changelist')
        url += "?id={}".format(obj.video.id)
        return format_html("<a href='{}'>{}</a>".format(url, text))

    def mp4(self, obj):
        url = "http://104.199.250.233/{}.mp4".format(obj.id)
        try:
            base = obj.m3u8.scenes[0]['start']
            st = round(obj.start, 2)
            ed = round(obj.end, 2)
            url = "http://104.199.250.233:8081/hls_to_mp4?m3u8_url=http%3A%2F%2F104.199.250.233%3A8000%2Fmaterial%2Fscene%2F{}.m3u8&duration={}~{}".format(obj.id, st, ed)
        except:
            pass

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

    def get_queryset(self, request):
        return super(VideoSceneAdmin, self).get_queryset(request).select_related('video')


class CollectionAdmin(admin.ModelAdmin):
    search_fields = ('name', 'text' )
    list_display = ('name', 'scenes', 'text', 'links', 'mp4')
    def links(self, obj):
        html = ""
        try:
            url = reverse('collection_m3u8', kwargs={'cid': obj.id})
            html += "<a Target='_new' href='{}'>{}</a><br/>".format(url, 'm3u8_url')
            url = reverse('collection_preview', kwargs={'cid': obj.id})
            html += "<a Target='_new' href='{}'>{}</a>".format(url, 'preview')
            return format_html(html)
        except Exception as e:
            print(e)


    def mp4(self, obj):
        url = "http://104.199.250.233/{}.mp4".format(obj.id)
        try:
            url = "http://104.199.250.233:8081/hls_to_mp4?m3u8_url=http%3A%2F%2F104.199.250.233%3A8000%2Fmaterial%2Fcollection%2F{}.m3u8".format(obj.id)
        except:
            pass

        return format_html("<a Target='_new' href='{}'>{}</a>".format(url, 'mp4'))

admin.site.register(Video, VideoAdmin)
admin.site.register(VideoScene, VideoSceneAdmin)
admin.site.register(Collection, CollectionAdmin)
