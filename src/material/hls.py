import urllib
import requests
import re
import tempfile
import os
import copy
import json

class M3U8:
    def __init__(self, headers, sences, base_url=""):
        self.headers = headers 
        self.sences = sences
        self.base_url = base_url

    def slince(self, st, ed):
        # slince hls
        result = {}
        sences = []
        new_idx=0
        for sence in copy.deepcopy(self.sences):
            if sence['start'] + sence['duration'] > st and sence['start'] < ed:
                sence['idx'] = new_idx
                sences.append(sence)
                new_idx += 1

        headers = self.headers
        sences = sences
        return M3U8(headers, sences, self.base_url)

    def select(self, idxs):
        idx = 0
        tmp = {}

        for sence in copy.deepcopy(self.sences):
            if sence['idx'] in idxs:
                tmp[sence['idx']] = sence
        
        sences = []
        new_idx = 0
        for idx in idxs:
            if tmp.get(idx, None):
                tmp[idx]['idx'] = new_idx
                sences.append(tmp[idx])
                new_idx += 1
        return M3U8(self.headers, sences, self.base_url)


    def render(self, clear=False):
        base_url = self.base_url
        context = ""
        context += self.headers
        sence_template = """
#EXTINF:{duration},{title}
{file_path}
        """.strip() + "\n"
        
        for sence in self.sences:
            file_path = sence['file_path']
            if clear:
                file_path = file_path.split('/')[-1]

            sence['file_path'] = file_path
            context += sence_template.format(**sence)

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
        sences = []

        # parse duration & title
        extinf = re.compile('^#EXTINF:([\d.]+),(.*)')

        # parse ts file path
        ts = re.compile('\n([^#].*)')

        raw_sences = datas[1:]
        st = 0
        idx = 0
        for raw_sence in raw_sences:
            duration, title = extinf.search(raw_sence).groups()
            file_path = ts.search(raw_sence).groups()[0]

            file_path = urllib.parse.urljoin(base_url, file_path)
            sence = {'title': title, 'duration': float(duration), "file_path":file_path, 'start': st, 'idx': idx}
            sences.append(sence)
            st+= sence['duration']
            idx += 1

        return M3U8.from_data(json.dumps({'headers': headers, 'sences': sences, 'base_url': base_url}))

    def create_m3u8_file(self, path):
        with open(path, 'w+') as f:
            f.write(self.render())
        return path

    def dump_data(self):
        data = {}
        data['headers'] = copy.deepcopy(self.headers)
        data['sences'] = copy.deepcopy(self.sences)
        data['base_url'] = copy.deepcopy(self.base_url)
        return json.dumps(data)

    @staticmethod
    def from_data(data):
        data = json.loads(data)
        return M3U8(data['headers'], data['sences'], data['base_url'])



def create_path(path):
    try:
        os.makedirs(path)
    except:
        pass

# todo
def download(url, output_path):
    create_path(output_path)
    cmd = "ffmpeg -protocol_whitelist \"file,http,https,tcp,tls\" -i {url} -f hls {output_path}".format(url=url, output_path=output_path)
    os.system(cmd)
    return output_path

# todo
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

if __name__ == '__main__':
    url = 'http://35.192.13.0:8000/J1神户1-0柏/video.m3u8'
    m3u8 = M3U8.from_url('http://35.192.13.0:8000/J1%E7%A5%9E%E6%88%B71-0%E6%9F%8F/video.m3u8')
    min_m3u8 = m3u8.slince(50, 100)
    new = m3u8.select([2,3,5,8,9])
    print(new.render())

def create_previews(hls_path, name_pattern="{}.jpg"):
    pass
