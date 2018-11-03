from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Video, VideoScene, Collection, Streaming
from django.urls import reverse
from django.utils.html import format_html
from datetime import timedelta
import json
import hashlib
from django.shortcuts import redirect
from material import tasks

def create_key(infos):
    m = hashlib.md5()
    for i in infos:
        m.update(str(i).encode('utf-8'))
    key = m.hexdigest()
    return key

class IdsFilter(admin.SimpleListFilter):
    title = 'Ids'
    parameter_name = 'ids'

    def lookups(self, request, model_admin):
        return ()

    def queryset(self, request, queryset):
        ids = request.GET.get(ids).split(',')
        return queryset.filter(id__in=ids)



class VideoAdmin(admin.ModelAdmin):
    class Media:
        js = ('js/admin/mymodel.js',)
    list_display = ('video_name', 'slice', 'links', 'scenes')
    list_filter = ('id', )
    readonly_fields = ('slice', 'links', 'scenes')

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

    list_display = ('id', 'status', 'tag_names', 'text', 'video__name', 'links', 'edit', 'mp4', 'start')

    list_filter = ('tags', IdsFilter,)
    search_fields = ('text', 'video__name' )
    actions = ('create_collection', )
    readonly_fields = ('links', 'edit', 'mp4', 'status')


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
        return format_html("<a Target='_new' href='{}'>{}</a>".format(url, text))

    def mp4(self, obj):
        url = "http://104.199.250.233/{}.mp4".format(obj.id)
        try:
            st = round(obj.start, 2)
            ed = round(obj.end, 2)
            key = create_key([st, ed])
            url = "http://104.199.250.233:8081/hls_to_mp4?m3u8_url=http%3A%2F%2F104.199.250.233%3A8000%2Fmaterial%2Fscene%2F{}.m3u8&cache_key={}".format(obj.id, key)
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
        queryset = super(VideoSceneAdmin, self).get_queryset(request).prefetch_related('video', 'tags')
        ids = request.GET.get('ids', "").strip()
        ids = ids and ids.split(',')
        if ids:
            queryset = queryset.filter(id__in=ids)
        return queryset

    def create_collection(self, request, queryset):
        scenes = ",".join([str(q.id) for q in queryset])
        collection = Collection.objects.create(name="{{輸入名稱}}", text="{{輸入敘述}}", scenes=scenes)
        return redirect('admin:material_collection_change', object_id=collection.id)
    create_collection.short_description = "合成錦集"

class CollectionAdmin(admin.ModelAdmin):
    search_fields = ('name', 'text' )
    list_display = ('name', 'status', 'scenes_link', 'text', 'links', 'mp4', 'video_names')
    readonly_fields = ('links', 'mp4')
    actions = ('publish',)
    list_filter = ('videos', )

    def get_queryset(self, request):
        queryset = super(CollectionAdmin, self).get_queryset(request).prefetch_related('videos')
        return queryset

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
            key = create_key(obj.scenes)
            url = "http://104.199.250.233:8081/hls_to_mp4?m3u8_url=http%3A%2F%2F104.199.250.233%3A8000%2Fmaterial%2Fcollection%2F{}.m3u8&cache_key={}".format(obj.id, key)
        except:
            pass

        return format_html("<a Target='_new' href='{}'>{}</a>".format(url, 'mp4'))

    def publish(self, request, queryset):
        ids = [q.id for q in queryset]
        tasks.sync_collections.delay(ids)

    def video_names(self, obj):
        vs = obj.videos.all()
        return format_html("<br>".join(["<a Target='_new' href='?videos__id__exact={}'>{}</a>".format(v.id, v.name) for v in vs]))

    def scenes_link(self, obj):
        scenes = obj.scenes.split(',')
        return format_html("<a Target='_new' href='/admin/material/videoscene/?ids={}'>{}</a>".format(",".join(scenes), "<br>".join(scenes)))




class StreamingAdmin(admin.ModelAdmin):
    list_display_links = []
    list_display = ['name', 'status', 'start', 'duration', '_urls']
    list_editable = ['_urls', 'duration', 'status']
    
#    list_editable = ['name', 'status', 'duration', 'url']
#    def get_readonly_fields(self, request, obj=None):
#        if obj: # editing an existing object
#            # All model fields as read_only
#            return self.readonly_fields + tuple([item.name for item in obj._meta.fields])
#        return self.readonly_fields


admin.site.register(Video, VideoAdmin)
admin.site.register(VideoScene, VideoSceneAdmin)
admin.site.register(Collection, CollectionAdmin)
admin.site.register(Streaming, StreamingAdmin)
