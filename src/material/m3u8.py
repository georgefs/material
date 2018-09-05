#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright © 2018 lizongzhe 
#
# Distributed under terms of the MIT license.
import re
import pprint

def quick_parse(f):
    datas = re.split('(?=#EXTINF)', f.read())
    headers = datas[0]
    sences = []

    # parse duration & title
    extinf = re.compile('^#EXTINF:([\d.]+),(.*)')

    # parse byterange
    byterange = re.compile('#EXT-X-BYTERANGE:(\d+)@(\d+)')

    # parse ts file path
    ts = re.compile('\n([^#].*)')

    raw_sences = datas[1:]
    st = 0
    for raw_sence in raw_sences:
        duration, title = extinf.search(raw_sence).groups()
        file_size, file_start = byterange.search(raw_sence).groups()
        file_path = ts.search(raw_sence).groups()[0]
        sence = {'title': title, 'duration': float(duration), "file_size": int(file_size), "file_start":file_start, "file_path":file_path, 'start': st}
        sences.append(sence)
        st+= sence['duration']

    return {'headers': headers, 'sences': sences}

def quick_format(data):
    m3u8 = ""
    m3u8 += data['headers']
    sence_template = """
#EXTINF:{duration},{title}
#EXT-X-BYTERANGE:{file_size}@{file_start}
{file_path}
    """.strip() + "\n"
    
    for sence in data['sences']:
        m3u8 += sence_template.format(**sence)

    m3u8 += "#EXT-X-ENDLIST"
    return m3u8

def quick_slince(data, st, ed):
    result = {}
    
    sences = []
    for sence in data['sences']:
        if sence['start'] + sence['duration'] > st and sence['start'] < ed:
            sences.append(sence)

    result['headers'] = data['headers']
    result['sences'] = sences
    return result

def download(m3u8_url, output_path):
    cmd = "ffmpeg -i \"{m3u8_url}\" -c copy {output_path}".format(m3u8_url=m3u8_url, output_path=output_path)
    os.system(cmd)


if __name__ == '__main__':
    with open('output.m3u8') as f:
        data = quick_parse(f)
        
        m3u8 = quick_format(data)

        data = quick_slince(data, 1000, 1200)
        print(quick_format(data))
        import pdb;pdb.set_trace()

