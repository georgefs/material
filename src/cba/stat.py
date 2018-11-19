#! /usr/bin/env python
# -*- coding: utf-8 -*-
import requests
import time
import hashlib

def get_sig():
     key = 'm722ptd7hh7kngk8d5w8gqbt'
     secret = 'SHpBwYhZG4'
     timestamp = repr(int(time.time()))
     key_info = (key + secret + timestamp).encode('ascii')
     signature = hashlib.sha256(key_info).hexdigest()
     params = {  'accept': 'json',
                 'api_key': key,
                 'sig': signature }
     return params

def get_pbps(event_id):
    api = "http://api.stats.com/v1/stats/basketball/cbachn/events/{}".format(event_id)
    params = {}
    params['pbp'] = True
    params['languageId'] = 3
    params['accept'] = "json"
    params.update(get_sig())
    data = requests.get(api.format(event_id), params=params).json()['apiResults'][0]['league']['season']['eventType'][0]['events'][0]

    return data['teams'], data['pbp']

def get_box(event_id):
    api = "http://api.stats.com/v1/stats/basketball/cbachn/box/{}".format(event_id)
    params = {}
    params['pbp'] = True
    params['languageId'] = 3
    params['accept'] = "json"
    params.update(get_sig())
    data = requests.get(api.format(event_id), params=params).json()['apiResults'][0]['league']['season']['eventType'][0]['events'][0]['boxscores']
    return data


def get_players():
    api = "http://api.stats.com/v1/stats/basketball/cbachn/participants/"

    params = {}
    params['pbp'] = True
    params['languageId'] = 3
    params['accept'] = "json"
    params.update(get_sig())
    return requests.get(api, params=params).json()['apiResults'][0]['league']['players']


def get_play_events():
    api = "http://api.stats.com/v1/decode/basketball/cbachn/playDetails"
    
    params = {}
    params['languageId'] = 3
    params['accept'] = "json"
    params.update(get_sig())
    return requests.get(api, params=params).json()['apiResults'][0]['league']['playEvents']
