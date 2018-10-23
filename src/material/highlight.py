#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright © 2018 lizongzhe 
#
# Distributed under terms of the MIT license.
import requests, re, json
def login():
    session = requests.Session()
    resp = session.get('http://35.229.222.200:8000/api-auth/login/?next=/studio/videos/')

    login_info = {}
    login_info['username'] = "george"
    login_info['password'] = "test1234"
    login_info.update({"csrfmiddlewaretoken": session.cookies['csrftoken']})

    resp = session.post('http://35.229.222.200:8000/api-auth/login/?next=/studio/videos/', data=login_info)
    print(resp)
    return session

def upload(data):
    session = login()
    resp = session.get('http://35.229.222.200:8000/studio/videos/')

    info = {}
    info['name'] = data['name']
    info['tags'] = data['tags']
    info['description'] = data['description']
    info['league'] = data['league']
    info.update({"csrfmiddlewaretoken": session.cookies['csrftoken']})

    files = {}
    files['cover_image'] = data['cover_image'] # open('cover.jpg', 'rb')
    files['file'] = data['file'] # open('tmp.mp4', 'rb')
    resp = session.post('http://35.229.222.200:8000/studio/videos/', data=info, files=files)
    return resp


