import urllib
import requests
import re
import tempfile
import os
import copy
import json
import subprocess


class M3U8:
    def __init__(self, headers, scenes, base_url=""):
        self.headers = headers
        self.scenes = scenes
        self.base_url = base_url

    def slice(self, st, ed):
        # slice hls
        result = {}
        scenes = []
        for scene in copy.deepcopy(self.scenes):
            if scene['start'] + scene['duration'] > st and scene['start'] < ed:
                scenes.append(scene)

        headers = self.headers
        scenes = scenes
        return M3U8(headers, scenes, self.base_url)

    @property
    def duration(self):
        t = 0
        for s in self.scenes:
            t += s['duration']
        return t

    @property
    def preview_image_template(self):
        file_path = self.scenes[0]['file_path']
        base = re.sub('video\d+.ts', '', file_path)
        return base + "video{}.ts.jpg"

    @property
    def scene_previews(self):
        for scene in self.scenes:
            yield(scene, scene['file_path'] + ".jpg")

    def select(self, idxs):
        idx = 0
        tmp = {}

        for scene in copy.deepcopy(self.scenes):
            if scene['idx'] in idxs:
                tmp[scene['idx']] = scene

        scenes = []
        new_idx = 0
        for idx in idxs:
            if tmp.get(idx, None):
                tmp[idx]['idx'] = new_idx
                scenes.append(tmp[idx])
                new_idx += 1
        return M3U8(self.headers, scenes, self.base_url)

    def render(self, clear=False, end=True):
        base_url = self.base_url
        context = ""
        context += self.headers
        if self.scenes:
            context = re.sub('#EXT-X-MEDIA-SEQUENCE:\d+', '#EXT-X-MEDIA-SEQUENCE:{}'.format(self.scenes[0]['idx']), context)

        scene_template = """
#EXT-X-DISCONTINUITY
#EXTINF:{duration},{title}
{file_path}
        """.strip() + "\n"

        for scene in self.scenes:
            file_path = scene['file_path']
            if clear:
                file_path = file_path.split('/')[-1]

            scene['file_path'] = file_path
            context += scene_template.format(**scene)

        if end:
            context += "#EXT-X-ENDLIST"
        return context

    @staticmethod
    def from_url(url):
        resp = requests.get(url)
        return M3U8.from_context(resp.text, url)

    @staticmethod
    def from_path(path, base_url=""):
        with open(path) as f:
            context = f.read()
            return M3U8.from_context(context, base_url)

    @staticmethod
    def from_context(context, base_url=""):
        datas = re.split('(?=#EXTINF)', context)
        headers = datas[0]
        scenes = []

        # parse duration & title
        extinf = re.compile('^#EXTINF:([\d.]+),(.*)')

        # parse ts file path
        ts = re.compile('\n([^#].*)')

        raw_scenes = datas[1:]
        st = 0
        idx = 0
        for raw_scene in raw_scenes:
            duration, title = extinf.search(raw_scene).groups()
            file_path = ts.search(raw_scene).groups()[0]

            file_path = urllib.parse.urljoin(base_url, file_path)
            scene = {'title': title, 'duration': float(duration), "file_path": file_path, 'start': st, 'idx': idx}
            scenes.append(scene)
            st += scene['duration']
            idx += 1

        return M3U8.from_data(json.dumps({'headers': headers, 'scenes': scenes, 'base_url': base_url}))

    def create_m3u8_file(self, path):
        with open(path, 'w+') as f:
            f.write(self.render())
        return path

    def dump_data(self):
        data = {}
        data['headers'] = copy.deepcopy(self.headers)
        data['scenes'] = copy.deepcopy(self.scenes)
        data['base_url'] = copy.deepcopy(self.base_url)
        return json.dumps(data)

    @staticmethod
    def from_data(data):
        data = json.loads(data)
        return M3U8(data['headers'], data['scenes'], data['base_url'])
    
    @staticmethod
    def concat(m3u8s):
        scenes = []
        headers = m3u8s[0].headers
        
        for m3u8 in m3u8s:
            scenes += m3u8.scenes

        idx = 0
        st = 0
        for scene in scenes:
            scene['idx'] = idx
            scene['start'] = st 
            st = st + scene['duration']
            scene['start'] = st

        return  M3U8.from_data(json.dumps({'headers': headers, 'scenes': scenes, 'base_url':''}))


def create_path(path):
    try:
        os.makedirs(path)
    except:
        pass


def download_to_mp4(m3u8, output_path):
    m3u8_path = urllib.parse.urljoin(output_path, "video.m3u8")
    m3u8.create_m3u8_file(m3u8_path)
    cmd = "ffmpeg -protocol_whitelist file,http,https,tcp,tls -i {m3u8_path} -c copy {output_path}".format(m3u8_path=m3u8_path, output_path=output_path)

    proc = subprocess.Popen(cmd.split())

    if delay:
        return proc
    else:
        proc.wait()


def to_hls(source, dist, preview=False, copycodec=False, delay=False):
    create_path(dist)
    cmd = "ffmpeg -i {source} -start_number 0 -hls_time 2 -hls_list_size 0 -g 1 -f hls {dist}/video.m3u8".format(source=source, dist=dist)
    if preview:
        cmd += " -vf fps=1/2 -start_number 0 {dist}/video%d.ts.jpg".format(dist=dist)

    logfile = open('/tmp/streaming_{}.log'.format(dist.split('/')[-1]), 'wb+')

    proc = subprocess.Popen(cmd.split(), stdout=logfile, stderr=logfile)

    if delay:
        return proc
    else:
        proc.wait()


