from django.shortcuts import render
from .models import Video, VideoScene
from django.urls import reverse
from django.http import HttpResponse

# Create your views here.


def video_m3u8(request, vid):
    obj = Video.objects.get(pk=vid).m3u8

    # format st_second~ed_second(int:int)
    duration = request.GET.get('duration', None)
    if duration:
        st, ed = duration.split('~')
        st, ed = int(st), int(ed)
        obj = obj.slince(st, ed)

    return HttpResponse(obj.render())

def scene_m3u8(request, vid):
    obj = VideoScene.objects.get(pk=vid).m3u8
    return HttpResponse(obj.render())

def video_preview(request, vid):
    m3u8_url = reverse('video_m3u8', kwargs={'vid':vid})
    return preview(m3u8_url)

def scene_preview(request, vid):
    m3u8_url = reverse('scene_m3u8', kwargs={'vid':vid})
    return preview(m3u8_url)

def preview(m3u8_url):
    template = '''
    <head>
	<script type="text/javascript" src="https://cdn.jsdelivr.net/npm/clappr@latest/dist/clappr.min.js"></script>
    </head>

    <body>
	<div id="player"></div>
	<script>
var player = new Clappr.Player({{source: "{m3u8_url}", parentId: "#player"}});
	</script>
    </body>
'''
    return HttpResponse(template.format(m3u8_url=m3u8_url))



def scene_preview_images(request, vid):
    template = '<img src="{}" width="200px">'
    obj = VideoScene.objects.get(pk=vid)
    images = obj.preview_images()
    m3u8_url = reverse('scene_m3u8', kwargs={'vid':vid})

    html = '''<head>
	<script type="text/javascript" src="https://cdn.jsdelivr.net/npm/clappr@latest/dist/clappr.min.js"></script>
    </head>'''


    html += '''
    <body>
	<div id="player"></div>
	<script>
var player = new Clappr.Player({{source: "{m3u8_url}", parentId: "#player"}});
	</script>
    </body>
    '''.format(m3u8_url=m3u8_url)

    html += '<div>{}</div>\n'.format(obj.text)
    for img in images:
        html += template.format(img)

    return HttpResponse(html)
