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
import logging
logger = logging.getLogger(__name__)

def preprocess(im):
    print('process')
    pixdata = im.load()
    for y in range(im.size[1]):
        for x in range(im.size[0]):
            if pixdata[x,y][0]>150 and pixdata[x,y][1]>150 and pixdata[x,y][2]>150:
                pixdata[x,y]=( 0, 0, 0, 0)
            else:
                pixdata[x,y]=(255, 255, 255, 0)

    return im

# 取得圖片 by url
def get_image(img_url):
    response = requests.get(img_url)
    # print(response.url)
    img = Image.open(BytesIO(response.content))
    return img

# 預測單行
def detect(img):
    il = img.crop((334, 561, 372, 585))
    il = img.crop((690, 920, 785, 964))
    ir = img.crop((335, 603, 371, 630))
    ir = img.crop((1040, 920, 1129, 964))

    #il, ir = preprocess(il), preprocess(ir)
    #display(il)
    #display(ir)
    #img_hashs = (imagehash.average_hash(il, hash_size=10), imagehash.average_hash(ir, hash_size=10))
    il, ir = preprocess(il), preprocess(ir)
    points = pytesseract.image_to_string(il, config='--psm 7'),pytesseract.image_to_string(ir, config='--psm 7')

    tmp = []
    for p in points:
        p = re.sub("[,.;‘)}:]", "", p).replace('A', '4').replace('Z', '2').replace('O', '0').replace('B', '8')
        tmp.append(p)
    print(points)
    return tuple(tmp)

# 確認 logo 
def is_activity(img):
    t = img.crop((1414, 922, 1455, 964))
    ori = imagehash.hex_to_hash('3c7af6fa4c3c7c3c')
    new_hash = imagehash.average_hash(t)
    return ori - new_hash <= 6


def predict(img_url):
    img = get_image(img_url)
    print(img_url)
    if is_activity(img):
        return detect(img)
    else:
        return None



def get_events(live_id, old_events=[]):
    t = datetime.now().strftime('%s000')
    api = 'http://api.sports.sina.com.cn/?p=live&s=livecast&a=livecastlogv3&format=json&key=l_{}&id={}&order=-1&num=10000&year=2014-03-05&callback=&dpc=1'
    # api = 'http://data.live.126.net/live/{}.json?_={}'
    if not old_events:
        # query for none id 
        oldest_event = {"id": ""}
    else:
        oldest_event = old_events[-1]

    old_events = list(reversed(old_events))

    new_events = []
    while True:
        try:
            url = api.format(live_id, oldest_event['id'])
            data = requests.get(url).json()['result']['data']
            if len(data) == 0:
                logger.info('cba api:{} success fetch {} message'.format(url, len(old_events)))
                break

            oldest_event = data[-1]
            new_events = new_events + data
        except Exception as e:
            logger.warning('cba api {} error {}'.format(url, e))
    logger.info('cba api fetch {}'.format(new_events))
    return list(reversed(old_events + new_events))
            
        



def get_players_tag(message):
    result = []
    for player, names in players.players.items():
        for name in names:
            if name in message:
                result.append((message.rfind(name), player))
                break
    if result:
        result = sorted(result, key=lambda x:x[0])
        print(result)
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
            "其他事件":["拉杆","擦板","补篮","挑篮","打板","勾手","反篮","干拔","反击","空切","跑投","强起","放篮","半截篮","放球","舔篮","放筐","上空篮","补进","打进","补中","两分"],
    }
    result = []
    for action, keywords in actions.items():
        for keyword in keywords:
            if keyword in message:
                result.append(action)
    if "罚" in message.replace('罚球线', ''):
        result.append('罚球')
    return result

def is_teams(team, player):
    if player in teams.teams[team]:
        return True
    else:
        return False

def is_star(player):
    return player in players.stars
