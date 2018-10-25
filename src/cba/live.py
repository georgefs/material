from datetime import datetime
import requests

def live_messages(live_id, old_events=[]):
    t = datetime.now().strftime('%s000')
    api = 'http://api.sports.sina.com.cn/?p=live&s=livecast&a=livecastlogv3&format=json&key=l_{}&id={}&order=-1&num=50&year=2014-03-05&callback=&dpc=1'
    # api = 'http://data.live.126.net/live/{}.json?_={}'
    
    requests.get()



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
