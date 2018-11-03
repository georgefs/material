from django.shortcuts import render
from .models import Video, VideoScene, Collection
from django.urls import reverse
from django.http import HttpResponse
from datetime import datetime
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.middleware import csrf
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from material.hls import M3U8


# Create your views here.

def video_streaming_m3u8(request, vid):
    time_format = "%Y-%m-%dT%H:%M:%S"
    start_time = request.GET.get('start_time', None)
    cycle_seconds = int(request.GET.get('cycle_seconds', '0')) # default 0
    buffer_seconds = int(request.GET.get('buffer_seconds', '300')) # default 300 sec

    start_time = datetime.strptime(start_time, time_format)

    obj = Video.objects.get(pk=vid).m3u8
    now = datetime.now()
    delta_time = (now - start_time).total_seconds()
    if cycle_seconds:
        current_streaming_seconds = delta_time % cycle_seconds
    else:
        current_streaming_seconds = delta_time
    if delta_time > 0:
        obj = obj.slice(current_streaming_seconds - buffer_seconds, current_streaming_seconds)
        return HttpResponse(obj.render(end=False))
    else:
        return HttpResponse('')


def video_m3u8(request, vid):
    obj = Video.objects.get(pk=vid).m3u8

    # format st_second~ed_second(int:int)
    duration = request.GET.get('duration', None)
    idxs = request.GET.get('idxs', None)
    if duration:
        st, ed = duration.split('~')
        st, ed = float(st), float(ed)
        obj = obj.slice(st, ed)
    elif idxs:
        idxs = idxs.split(',')
        idxs = [int(i) for i in idxs if i.strip()]
        obj = obj.select(idxs)


    return HttpResponse(obj.render())


def scene_m3u8(request, vid):
    obj = VideoScene.objects.get(pk=vid).m3u8
    return HttpResponse(obj.render())

def collection_m3u8(request, cid):
    obj = Collection.objects.get(pk=cid).m3u8
    return HttpResponse(obj.render())


def video_preview(request, vid):
    m3u8_url = reverse('video_m3u8', kwargs={'vid': vid})

    template = '''
    <head>
            <script type="text/javascript" src="https://cdn.jsdelivr.net/npm/clappr@latest/dist/clappr.min.js"></script>
            <script>window.clappr = Clappr;</script>
            <script type="text/javascript" src="https://cdn.jsdelivr.net/npm/clappr-playback-rate-plugin@0.4.0/lib/clappr-playback-rate-plugin.min.js"></script>
            <script>window.PlaybackRatePlugin = window['clappr-playback-rate-plugin'].default</script>
    </head>

    <body>
        <div id="player"></div>
        <script>
                 var player = new Clappr.Player({{source: "{m3u8_url}", parentId: "#player", plugins: {{'core': [PlaybackRatePlugin]}}}});
        </script>
    </body>
    '''
    return HttpResponse(template.format(m3u8_url=m3u8_url))


def scene_preview(request, vid):
    m3u8_url = reverse('scene_m3u8', kwargs={'vid': vid})

    template = '''
    <head>
            <script type="text/javascript" src="https://cdn.jsdelivr.net/npm/clappr@latest/dist/clappr.min.js"></script>
            <script>window.clappr = Clappr;</script>
            <script type="text/javascript" src="https://cdn.jsdelivr.net/npm/clappr-playback-rate-plugin@0.4.0/lib/clappr-playback-rate-plugin.min.js"></script>
            <script>window.PlaybackRatePlugin = window['clappr-playback-rate-plugin'].default</script>

    </head>

    <body>
        <div id="player"></div>
        <script>
                 var player = new Clappr.Player({{source: "{m3u8_url}", parentId: "#player", plugins: {{'core': [PlaybackRatePlugin]}}}});
        </script>
    </body>
    '''
    return HttpResponse(template.format(m3u8_url=m3u8_url))


def collection_preview(request, cid):
    m3u8_url = reverse('collection_m3u8', kwargs={'cid': cid})

    template = '''
    <head>
            <script type="text/javascript" src="https://cdn.jsdelivr.net/npm/clappr@latest/dist/clappr.min.js"></script>
            <script>window.clappr = Clappr;</script>
            <script type="text/javascript" src="https://cdn.jsdelivr.net/npm/clappr-playback-rate-plugin@0.4.0/lib/clappr-playback-rate-plugin.min.js"></script>
            <script>window.PlaybackRatePlugin = window['clappr-playback-rate-plugin'].default</script>

    </head>

    <body>
        <div id="player"></div>
        <script>
                 var player = new Clappr.Player({{source: "{m3u8_url}", parentId: "#player", plugins: {{'core': [PlaybackRatePlugin]}}}});
        </script>
    </body>
    '''
    return HttpResponse(template.format(m3u8_url=m3u8_url))

class VideoSlinceView(View):
    def get(self, request, vid):
        v = Video.objects.get(pk=vid)

        obj = Video.objects.get(pk=vid)
        m3u8_url = reverse('video_m3u8', kwargs={'vid': vid})
        html = '''<head>
            <script type="text/javascript" src="https://cdn.jsdelivr.net/npm/clappr@latest/dist/clappr.min.js"></script>
            <script>window.clappr = Clappr;</script>
            <script type="text/javascript" src="https://cdn.jsdelivr.net/npm/clappr-playback-rate-plugin@0.4.0/lib/clappr-playback-rate-plugin.min.js"></script>
            <script>window.PlaybackRatePlugin = window['clappr-playback-rate-plugin'].default</script>
        </head>'''
        html += '''
        <body>
            <div id="player"></div>
            <script>
                 var player = new Clappr.Player({{source: "{m3u8_url}", parentId: "#player", plugins: {{'core': [PlaybackRatePlugin]}}}});
                 var base = {base};
                 function set_start(){{
                   elem = document.getElementById('start');
                   elem.value = player.getCurrentTime().toFixed(2) + base;
                 }}

                 function set_end(){{
                   elem = document.getElementById('end');
                   elem.value = player.getCurrentTime().toFixed(2) + base;
                 }}
            </script>
            <a href="#" onclick="set_start()">start</a>
            <a href="#" onclick="set_end()">end</a>
            <form method='post' action=''>
               <input type='text' name='text' >
               <input type='text' name='start' id='start' value='0'>
               <input type='text' name='end' id='end' value='0'>
               <input type='hidden' name="csrfmiddlewaretoken" value="{csrf}">
               <input type='submit' value='submit'>
            </form>
        </body>
        '''.format(m3u8_url=m3u8_url, base=v.m3u8.scenes[0]['start'], csrf=csrf.get_token(request))

        template = '<a href="#" onclick="player.seek({});"><img src="{}" width="200px">'
        start = 0
        for scene in obj.m3u8.scenes[::5]:
            img = "{}.jpg".format(scene['file_path'])
            start = scene['start']
            html += template.format(start, img)

        return HttpResponse(html)

    @csrf_exempt
    def post(self, request, vid):
        st = float(request.POST.get('start'))
        ed = float(request.POST.get('end'))
        meta = request.POST.get('meta', '{}')
        text = request.POST.get('text', '')
        v = Video.objects.get(pk=vid)
        scene = v.slice(text, st, ed, meta,)

        return redirect('scene_edit', vid=scene.id)


class SceneEditorView(View):
    def get(self, request, vid):
        v = VideoScene.objects.get(pk=vid)

        template = '<a href="#" onclick="player.seek({});"><img src="{}" width="200px">'
        obj = VideoScene.objects.get(pk=vid)
        m3u8_url = reverse('scene_m3u8', kwargs={'vid': vid})

        html = '''<head>
            <script type="text/javascript" src="https://cdn.jsdelivr.net/npm/clappr@latest/dist/clappr.min.js"></script>
            <script>window.clappr = Clappr;</script>
            <script type="text/javascript" src="https://cdn.jsdelivr.net/npm/clappr-playback-rate-plugin@0.4.0/lib/clappr-playback-rate-plugin.min.js"></script>
            <script>window.PlaybackRatePlugin = window['clappr-playback-rate-plugin'].default</script>
        </head>'''
        html += '''
        <body>
            <div id="player"></div>
            <script>
                 var player = new Clappr.Player({{source: "{m3u8_url}", parentId: "#player", plugins: {{'core': [PlaybackRatePlugin]}}}});
                 var base = {base};
                 function set_start(){{
                   elem = document.getElementById('start');
                   elem.value = player.getCurrentTime() + base;
                 }}

                 function set_end(){{
                   elem = document.getElementById('end');
                   elem.value = player.getCurrentTime() + base;
                 }}
            </script>
            <a href="#" onclick="set_start()">start</a>
            <a href="#" onclick="set_end()">end</a>
            <form method='post' action=''>
               <input type='text' name='start' id='start' value='{st}'>
               <input type='text' name='end' id='end' value='{ed}'>
               <input type='hidden' name="csrfmiddlewaretoken" value="{csrf}">
               <input type='submit' value='submit'>
            </form>
        </body>
        '''.format(m3u8_url=m3u8_url, st=v.start, ed=v.end, base=v.m3u8.scenes[0]['start'], csrf=csrf.get_token(request))

        html += '<div>{}</div>\n'.format(obj.text)
        start = 0
        for scene in obj.m3u8.scenes:
            img = "{}.jpg".format(scene['file_path'])
            html += template.format(start, img)
            start += scene['duration']

        return HttpResponse(html)
    @csrf_exempt
    def post(self, request, vid):
        st = float(request.POST.get('start'))
        ed = float(request.POST.get('end'))
        v = VideoScene.objects.get(pk=vid)
        v.start = st
        v.end = ed
        v.save()
        return self.get(request, vid)


def get_uncheck_video(block_time=300):
    try:
        value = PubSub.sub('uncheck_videoscene')
    except:
        with CacheLock('fill_queue'):
            try:
                value = PubSub.sub('uncheck_videoscene')
            except:
                uncheck_videoscenes = VideoScene.objects.filter(status='init').values('id')
                uncheck_videoscene_ids = [v['id'] for v in uncheck_videoscenes if not cache.get("lock_{}".format(v['id']), False)]
                uncheck_videoscene_ids = list(set(uncheck_videoscene_ids))
                value = None
                if uncheck_videoscene_ids:
                    value, queued = uncheck_videoscene_ids[0], uncheck_videoscene_ids[1:]
                    PubSub.pub_multi('uncheck_videoscene', uncheck_videoscene_ids[1:], unique=True)
    cache.set("lock_{}".format(value), True, block_time)
    return value

from cache_pubsub import PubSub, CacheLock
from django.core.cache import cache

class ReviewVideoSceneView(View):
    def get(self, request):
        response = HttpResponse()

        if not request.COOKIES.get('checking', None):
            vid = get_uncheck_video()
            response.set_cookie("checking", vid, 300)
        else:
            vid = request.COOKIES['checking']

        vc = VideoScene.objects.get(pk=vid)
        m3u8_url = reverse('video_m3u8', kwargs={'vid': vc.video.id})
        html = '''<head>
            <script type="text/javascript" src="https://cdn.jsdelivr.net/npm/clappr@latest/dist/clappr.min.js"></script>
            <script>window.clappr = Clappr;</script>
            <script type="text/javascript" src="https://cdn.jsdelivr.net/npm/clappr-playback-rate-plugin@0.4.0/lib/clappr-playback-rate-plugin.min.js"></script>
            <script>window.PlaybackRatePlugin = window['clappr-playback-rate-plugin'].default</script>
            <script>
                function shift_time(second){
                   var end = document.getElementById('end');
                   var start = document.getElementById('start');
                   end.value = parseInt(end.value) + parseInt(second);
                   start.value = parseInt(start.value) + parseInt(second);
                   render()
                }
                function render(){
                   var end = document.getElementById('end').value;
                   var start = document.getElementById('start').value;
                   var url = m3u8_url + "?duration=" + start + "~" + end;
                   console.log(url);
                   player.configure({"source": url});
                   player.play()
                }
            </script>
        </head>'''
        html += '''
        <body>
	    <b>{name}</b>
            <div id="player"></div>
            <p>{tags}</p>
            <a href="#" onclick="shift_time(-2)">前移2秒</a>
            <a href="#" onclick="shift_time(+2)">後移2秒</a>
            <form method='post' action=''>
               <input type='hidden' name='start' id='start' value='{st}'>
               <input type='hidden' name='end' id='end' value='{ed}'>
               <input type='hidden' name="csrfmiddlewaretoken" value="{csrf}">
               <input type='submit' name="status" value='approve'>
               <input type='submit' name="status" value='reject'>
            </form>

            <script>
                 var m3u8_url = "{m3u8_url}";
                 var player = new Clappr.Player({{source: "", parentId: "#player", plugins: {{'core': [PlaybackRatePlugin]}}}});
                 render()
            </script>

        </body>
        '''.format(m3u8_url=m3u8_url, st=vc.start, ed=vc.end, csrf=csrf.get_token(request), name=vc.text, tags=", ".join([t.name for t in vc.tags.all()]))

        response.content = html
        return response

    @csrf_exempt
    def post(self, request):
        response = redirect("review_videoscene")
        vid = request.COOKIES["checking"]
        vc = VideoScene.objects.get(pk=vid)
        vc.status = request.POST.get("status")
        vc.start = request.POST.get("start")
        vc.end = request.POST.get("end")
        vc.save()
        response.delete_cookie("checking")
        return response
