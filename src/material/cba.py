#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright © 2018 lizongzhe 
#
# Distributed under terms of the MIT license.
from datetime import datetime
import requests
from . import players
from . import teams
from PIL import Image
from io import BytesIO
import imagehash
import pytesseract
import re
import time
from django.core.cache import cache

# 取得圖片 by url
def get_image(img_url):
    response = requests.get(img_url)
    # print(response.url)
    img = Image.open(BytesIO(response.content))
    return img

# 預測單行
def detect(img):
    il = img.crop((334, 561, 372, 585))
    ir = img.crop((335, 603, 371, 630))
    #il, ir = preprocess(il), preprocess(ir)
    #display(il)
    #display(ir)
    #img_hashs = (imagehash.average_hash(il, hash_size=10), imagehash.average_hash(ir, hash_size=10))
    points = pytesseract.image_to_string(il, config='--psm 7'),pytesseract.image_to_string(ir, config='--psm 7')

    tmp = []
    for p in points:
        p = re.sub("[,.;‘)}:]", "", p).replace('A', '4').replace('Z', '2')
        tmp.append(p)
    print(points)
    return tuple(points)

# 確認 logo 
def is_activity(img):
    t = img.crop((149, 569, 195, 636))
    ori = imagehash.hex_to_hash('7cfef7586c003c00')
    new_hash = imagehash.average_hash(t)
    return ori - new_hash <= 3


def predict(img_url):
    img = get_image(img_url)
    print(img_url)
    if is_activity(img):
        return detect(img)
    else:
        return None

def get_events(live_id):

    result = []
    idx = 1
    while True:
        events = get_page_events(live_id, idx)
        if events:
            result += events
        else:
            break
        idx+=1
    return result


def get_page_events(live_id, idx):
    key = "{}_{}_{}".format("get_events", live_id, idx)
    if cache.get(key, None):
        return cache.get(key)


    t = datetime.now().strftime('%s000')
    api = 'http://data.live.126.net/liveAll/{}/{}.json?&_={}'
    data = []
    for i in range(3):
        try:
            resp = requests.get(api.format(live_id, idx, t))
            if resp.status_code == 200:
                data = []
                if len(resp.content) > 0:
                    data = resp.json()['messages']

                if len(data) >= 20:
                    cache.set(key, data, 10800)
                break
        except Exception as e:
            print(e)

    return data

def get_players_tag(message):
    result = []
    for player, names in players.players.items():
        for name in names:
            if name in message:
                result.append((message.index(name), player))
                break
    if result:
        result = sorted(result, key=lambda x:x[0])
        result = [v[1] for v in result]
    return result


def get_action_tags(message):
    actions = {
            "灌篮":["暴扣","扣"],
            "三分":["三分","3分"],
            "上篮":["上篮"],
            "快攻":["快攻"],
            "中距离":["中距离","中投","踩线"],
            "篮下":["篮下强攻","篮下","放进","强打"],
            "射篮":["跳投","抛投","投了","投一发","后仰","抛射","骑射","骑马射箭","强投","射一发"],
            "其他事件":["拉杆","擦板","罚","补篮","挑篮","打板","勾手","反篮","干拔","反击","空切","跑投","强起","放篮","半截篮","放球","舔篮","放筐","上空篮","补进","打进","补中","两分"],
    }
    result = []
    for action, keywords in actions.items():
        for keyword in keywords:
            if keyword in message:
                result.append(action)
    return result

def is_teams(team, player):
    if player in teams.teams[team]:
        return True

def is_star(player):
    return player in players.stars
