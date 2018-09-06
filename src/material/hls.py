import urllib
import requests
import re
import tempfile
import os
import copy
import json


class M3U8:
    def __init__(self, headers, scenes, base_url=""):
        self.headers = headers
        self.scenes = scenes
        self.base_url = base_url

    def slince(self, st, ed):
        # slince hls
        result = {}
        scenes = []
        for scene in copy.deepcopy(self.scenes):
            if scene['start'] + scene['duration'] > st and scene['start'] < ed:
                scenes.append(scene)

        headers = self.headers
        scenes = scenes
        return M3U8(headers, scenes, self.base_url)

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


def create_path(path):
    try:
        os.makedirs(path)
    except:
        pass


def download(url, output_path):
    create_path(output_path)
    cmd = "ffmpeg -protocol_whitelist \"file,http,https,tcp,tls\" -i {url} -f hls {output_path}".format(url=url, output_path=output_path)
    os.system(cmd)
    return output_path


def download_to_mp4(m3u8, output_path):
    m3u8_path = urllib.parse.urljoin(output_path, "video.m3u8")
    m3u8.create_m3u8_file(m3u8_path)
    cmd = "ffmpeg -protocol_whitelist \"file,http,https,tcp,tls\" -i \"{m3u8_path}\" -c copy {output_path}".format(m3u8_path=m3u8_path, output_path=output_path)
    os.system(cmd)
    return output_path


def download_from_mp4(source_url, output_path):
    create_path(output_path)
    m3u8_path = os.path.join(output_path, 'video.m3u8')
    cmd = "ffmpeg -protocol_whitelist \"file,http,https,tcp,tls\" -i {} -f hls {}".format(source_url, m3u8_path)
    os.system(cmd)
    return output_path


def to_hls(source, dist):
    cmd = "ffmpeg -i {source}  -profile:v baseline -level 3.0 -s 640x360 -start_number 0 -hls_list_size 0 -f hls {dist}/video.m3u8".format(source=source, dist=dist)
    os.system(cmd)


def create_previews(hls_path, name_pattern="{}.jpg"):
    for root, folders, files in os.walk(hls_path):
        for f in files:
            filepath = os.path.join(root, f)
            if filepath.endswith('.ts'):
                cmd = "ffmpeg -i {} -vframes 1  {}".format(filepath, name_pattern.format(filepath))
                os.system(cmd)
