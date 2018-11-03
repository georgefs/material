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
    logger.info(img_url)
    response = requests.get(img_url)
    # print(response.url)
    img = Image.open(BytesIO(response.content))
    return img


def resize(origin_size, target_size, bound):
    pw = target_size[0] / origin_size[0]
    ph = target_size[1] / origin_size[1]
    return (round(bound[0]*pw), round(bound[1]*ph), round(bound[2]*pw), round(bound[3]*ph))

# 預測單行
def detect(img):
    os = (1920, 1080)
    cs = img.size
    
    il = img.crop((334, 561, 372, 585))
    il = img.crop(resize(os, cs, (690, 920, 785, 964)))
    ir = img.crop((335, 603, 371, 630))
    ir = img.crop(resize(os, cs, (1040, 920, 1129, 964)))

    #il, ir = preprocess(il), preprocess(ir)
    #display(il)
    #display(ir)
    #img_hashs = (imagehash.average_hash(il, hash_size=10), imagehash.average_hash(ir, hash_size=10))
    # il, ir = preprocess(il), preprocess(ir)
    points = pytesseract.image_to_string(il, config='--psm 7 -l number'),pytesseract.image_to_string(ir, config='--psm 7 -l number')

    tmp = []
    for p in points:
        p = re.sub("[,.;‘)}:]", "", p).replace('A', '4').replace('Z', '2').replace('O', '0').replace('B', '8')
        tmp.append(p)
    print(points, 'detect')
    return tuple(tmp)

# 確認 logo 
def is_activity(img):
    os = (1920, 1080)
    cs = img.size

    t = img.crop((1414, 922, 1455, 964))
    t = img.crop(resize(os, cs, (1404, 922, 1465, 964)))
    ori = imagehash.hex_to_hash('183c3c7c3c2c383c')
    new_hash = imagehash.average_hash(t)
    return ori - new_hash <= 9


def predict(img_url):
    try:
        img = get_image(img_url)
    except:
        logger.warning("predict image {} error ".format(img_url))
        return None

    if is_activity(img):
        return detect(img)
    else:
        return None

