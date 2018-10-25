import logging
import json
from . import cba
from material.models import Video, VideoScene, Collection, Tag, Streaming
from multiprocessing import Pool
from django.db import  transaction

from django.db.models import Count

from collections import Counter

# Get an instance of a logger
logger = logging.getLogger(__name__)

from celery_queue import app
import time
import traceback
from datetime import datetime
import traceback

@app.task
def live(sid, f=False):
    logger.info('start video live {}'.format(sid))

    from material.models import Video

    with transaction.atomic():
        streaming = Streaming.objects.get(pk=sid)
        if not f:
            assert streaming.status == 'init'
        streaming.status = 'live'
        streaming.save()

    video = streaming.video
    print(video)
    proc = streaming.start_live(copycodec=True, delay=True)

    start = datetime.now()

    tagger_job = tagger.delay(sid)
    c = 0
    while True:
        returncode = proc.poll()
        # returncode != 0
        if returncode:
            streaming.status = 'fails'
            logging.info('video live {} fails {}'.format(sid, returncode))
            break
        elif returncode == 0:
            streaming.status = 'done'
            logging.info('video live {} end'.format(sid))
            break
        elif streaming.duration and (datetime.now() - start).total_seconds() >= streaming.duration:
            p.send_signal(9)
            streaming.status = 'done'
            logging.info('video live duration {} end'.format(sid))
            break
        else:
            c+=1
            # time.sleep(1)
            try:
                job = tagger(video.id)
                pass
            except Exception as e:
                print(e)
                pass
            except BaseException as e:
                print(e)
            # job.wait()
            continue
    
    job = tagger.delay(video.id)
    job.wait()

    video.load_info(video.direct_url)
    video.save()
    

def kv_exchange(d):
    k, v = d.keys(), d.values()
    return dict(v, k)

def point_hash(p):
    if type(p) == str:
        return p
    else:
        p = [str(s) for s in p]
        return json.dumps(p)

@app.task
def tagger(vid, end=False):
    print("start tagger {}".format(vid))
    try:
        v = Video.objects.get(pk=vid)
        meta = json.loads(v.meta)
        live_id = meta.get('live_id')
        events = meta.get('events', [])
        logs = meta.get('logs', []) # (time(second * 1/2), points)
        matcheds = meta.get('matcheds', [])
        home_team = meta.get('home_team', "")
        away_team = meta.get('away_team', "")

        matcheds_dict = dict([(point_hash(v[0]), v[1]) for v in matcheds])
        time_mappings = dict(logs)

        m3u8 = v.m3u8

        image_template = m3u8.preview_image_template

        for key in range(0, round(int(m3u8.duration//2))):
            if time_mappings.get(key, False) == False:
                time_mappings[key] = cba.predict(image_template.format(key))
        point_mappings = dict(sorted([(point_hash(v[1]), v[0]) for v in time_mappings.items() if v[1]], key=lambda x:-x[1]))

        events = cba.get_events(live_id, events)

        section_mappings ={
            0: "section_1",
            1: "section_1",
            2: "section_2",
            3: "section_3",
            4: "section_4",
        }
        last_score_event_idx = 0
        for event_idx, event in enumerate(events):
            last_point = (0, 0)
            c = 1
            while True:
                l_event = events[event_idx-c]
                try:
                    last_point = (int(l_event['s']['s1']), int(l_event['s']['s2']))
                    break
                except:
                    pass
                if event_idx - c == 0:
                    break
                c+=1 

            if not event.get('s', None):
                continue

            point = int(event['s']['s1']), int(event['s']['s2'])
            key = point_hash(point)
            msg = event['m']

            if not matcheds_dict.get(key, False) and point_mappings.get(key, False):
                start_idx = point_mappings[key]
                start = start_idx * 2

                for i in range(min(30, start_idx)):
                    if time_mappings[start_idx - 1 -i]:
                        break
                not_point_frames = i



                print(last_score_event_idx, 'last:')
                merged_msg = "\n".join([events[i]['m'] for i in range(last_score_event_idx, event_idx+1) if events[i].get('m')])
                print(len(merged_msg))
                actions = cba.get_action_tags(msg)
                msg = merged_msg


                score_team = None
                score_point = 0 
                if point[0] != (last_point[0]) and point[1] != (last_point[1]):
                    pass
                else:
                    if point[0] != last_point[0]:
                        score_team = home_team
                        score_point = point[0] - last_point[0]
                    else:
                        score_team = away_team
                        score_point = point[1] - last_point[1]

                tags = []
                players = cba.get_players_tag(merged_msg)
                score_player = None
                # player
                for idx, p in reversed(players):
                    t, _ = Tag.objects.get_or_create(name='{}_player'.format(p))
                    tags.append(t)

                    #print(cba.is_teams(score_team, p), score_team, p, msg.split('\n')[-1])
                    if score_team and not score_player and cba.is_teams(score_team, p):
                        t, _ = Tag.objects.get_or_create(name='{}_score_player'.format(p))
                        score_player = p
                        tags.append(t)
                        msg = msg[msg.rfind('\n', 0, idx):]
                    # print(score_player)

                if len(players) == 1:
                    t, _ = Tag.objects.get_or_create(name='{}_score_player'.format(p))
                    score_player = p
                    tags.append(t)

                # action
                for a in actions:
                    t, _ = Tag.objects.get_or_create(name='{}_event'.format(a))
                    tags.append(t)

                t, _ = Tag.objects.get_or_create(name='{}_score'.format(score_team))
                tags.append(t)

                # section number
                section_tag = section_mappings.get(event['q'], None)
                if section_tag:
                    t, _ = Tag.objects.get_or_create(name=section_tag)
                    tags.append(t)

                # score team
                if score_team:
                    t, _ = Tag.objects.get_or_create(name="{}_score".format(score_team))
                    tags.append(t)

                if not_point_frames > 4:
                    t, _ = Tag.objects.get_or_create(name="unsafe")
                    tags.append(t)


                scene_meta = {}
                scene_meta['score'] = score_point
                scene_meta['teams'] = [home_team, away_team]
                scene_meta['point'] = point
                scene_meta['score_team'] = score_team
                scene_meta['score_player'] = score_player
                scene_meta['event'] = event


                VideoScene.objects.filter(video=v, text=key + msg).delete()
                # scene duration
                if "罚" in msg.replace("罚球线", ""):
                    scene = v.slice(key + msg, start - 30 , start, meta=json.dumps(scene_meta))
                else:
                    scene = v.slice(key + msg, start -5 , start, meta=json.dumps(scene_meta))

                scene.tags.add(*tags)

                # tag mache successed
                matcheds_dict[key] = start
                if point != last_point:
                    print('point change', last_score_event_idx, point, last_point, event_idx)
                    last_score_event_idx = event_idx
                    last_point = point
                
    except Exception as e:
        traceback.print_exc()

    finally:
        meta['events'] = events
        meta['logs'] = [v for v in time_mappings.items()]
        meta['matcheds'] = [v for v in matcheds_dict.items()]
        meta['home_team'] = home_team
        meta['away_team'] = away_team
        

        v.meta = json.dumps(meta)
        v.save()

        sections = [
           2,
           3,
           4
        ]
        c = 0
        for event in events:
            
            if sections and event.get('q', None) == sections[0]:
                # print(event['q'] , sections[0])
                c+= 1
                point = event['s']['s1'], event['s']['s2']
                create_collections(v.id, c, point)
                sections = sections[1:]
                
        if end:
            c+=1
            point = event['s']['s1'], event['s']['s2']
            create_collections(v.id, c, point)

def process_queryset(qs):
    scene_ids = set([s.id for s in qs])
    scenes = VideoScene.objects.filter(id__in=scene_ids)
    return scenes

@app.task
def create_collections(vid, section, point=None):
    v = Video.objects.get(pk=vid)
    queryset = VideoScene.objects.filter(video=v).select_related()
    meta = json.loads(v.meta)
    home_team = meta['home_team']
    away_team = meta['away_team']
    section = str(section)

    processed_sections = meta.get('processed_sections', [])
    if str(section) in processed_sections:
        return

#    logs = meta['logs']
#    Counter(zip(*logs)[1])

    suffix = "{0}{2[0]}-{2[1]}{1}".format(home_team, away_team, point)
    
    def highlight_collection(queryset, section_name, size=8):
        name = "【{}集锦】{}".format(section_name, suffix)
        queryset = query_highlight(queryset)[:size]

        events = extract_events(queryset)
        tags = ["CBA","篮球", home_team, away_team ,"精彩","集锦"]
        tags += events

        ids = to_ids(queryset)
        # hightlight
        collection, _ = Collection.objects.get_or_create(
            name = name,        
        )
        collection.scenes = ",".join(ids)
        collection.meta = json.dumps(tags)
        collection.save()

        return collection

    def three_point_collection(queryset, section_name):
        queryset = query_three_point(queryset)
        team_info = split_by_team(queryset)
        result = []
        for team, scenes in team_info.items():
            name = "【{}{}三分实录】{}".format(team, section_name, suffix)
            three_point_scenes = query_three_point(scenes)
            ids = to_ids(three_point_scenes)
            collection, _ = Collection.objects.get_or_create(
                name = name,
            )

            tags = ["CBA","篮球",team,"三分","精彩","集锦"]

            collection.scenes = ",".join(ids)
            collection.meta = json.dumps(tags)
            collection.save()
            result.append((team, collection))
        return result

    def score_king_collection(queryset, section_name):
        player_scores = order_player(queryset)
        if not player_scores:
            return
        player, score = player_scores[0]
        queryset = queryset.exclude(tags__name='罚球_event').exclude(tags__name='unsafe')
        score_scenes = query_tag(queryset, "{}_score_player".format(player))
        ids = to_ids(score_scenes)
        name = "【{}】{}分 {}得分王 {}".format(player, score, section_name, suffix)

        tags = ["CBA","篮球","两队队名", player,"得分王","精彩","集锦"]
        events = extract_events(score_scenes)
        tags += events

        collection, _ = Collection.objects.get_or_create(
            name = name,
        )
        collection.scenes = ",".join(ids)
        collection.meta = json.dumps(tags)
        collection.save()
        return collection

    def star_collections(queryset):
        # ignore max
        teams=  split_by_team(queryset)
    
        cs = []
        for team, scenes in teams.items():
            team_queryset = process_queryset(scenes)
            player_scores = order_player(team_queryset)
            stars = []
            ps = []
            for player, score in player_scores:
                if cba.is_star(player):
                    stars.append(player)
                else:
                    ps.append(player)
            c = 0
            for player in (stars + ps):
                if c >= 2:
                    break


                team_queryset = team_queryset.exclude(tags__name='罚球_event').exclude(tags__name='unsafe')
                if not team_queryset:
                    continue
                score_scenes = query_tag(team_queryset, "{}_score_player".format(player))
                ids = to_ids(score_scenes)

                tags = ["CBA","篮球", home_team, away_team,"人名","精彩","集锦"]
                events = extract_events(score_scenes)
                tags += events

                name = "【{}】全场集锦 {}".format(player, suffix)
                collection, _ = Collection.objects.get_or_create(
                    name = name,
                )
                collection.scenes = ",".join(ids)
                collection.meta = json.dumps(tags)
                collection.save()
                cs.append(collection)
                c+= 1

        return cs


    section_mapping = {
        "1": "首节",
        "2": "第二节",
        "3": "第三节",
        "4": "第四节",
    }
    section_name = section_mapping[section]
    section_scenes = queryset.filter(tags__name='section_{}'.format(section))

    section_highlight = highlight_collection(section_scenes, section_name)
    section_three_point = three_point_collection(section_scenes, section_name)

    if section == "2":
        half_scenes = queryset.filter(tags__name__regex='section_[12]')
        section_name = "上半场"
        half_highlight = highlight_collection(half_scenes, section_name)
        half_three_point = three_point_collection(half_scenes, section_name)
        half_score_king = score_king_collection(half_scenes, section_name)

    if section == "4":
        full_scenes = queryset
        section_name = "全场"
        full_highlight = highlight_collection(full_scenes, section_name)
        full_three_point = three_point_collection(full_scenes, section_name)
        full_score_king = score_king_collection(full_scenes, section_name)
        stars = star_collections(full_scenes)

    processed_sections.append(section)

    meta['processed_sections'] = processed_sections
    v.meta = json.dumps(meta)
    v.save()
    cs = Collection.objects.filter(status='init')
    #sync_collections.delay([c.id for c in cs])
    

def extract_events(queryset):
    queryset = process_queryset(queryset)

    result = queryset.filter(tags__name__endswith='_event').values('tags__name').distinct()
    result = [r['tags__name'].replace('_event', '') for r in result]
    return result

def query_tag(queryset, tag):
    queryset = process_queryset(queryset)
    return queryset.filter(tags__name__contains=tag)

# 灌篮>三分>快攻>其他
def query_highlight(queryset):
    queryset = process_queryset(queryset)
    highlight = []
    result = []
    tmp = []
    queryset = queryset.exclude(tags__name='罚球_event').exclude(tags__name='unsafe')
    # ordered
    highlight = list(queryset.filter(tags__name='灌篮_event'))
    highlight += list(queryset.filter(tags__name='三分_event'))
    highlight += list(queryset.filter(tags__name='快攻_event'))
    highlight += list(queryset.filter(tags__name='上篮_event'))
    for h in highlight:
        if h.id not in tmp:
            result.append(h)
            tmp.append(h.id)
    return result

def query_three_point(queryset):
    queryset = process_queryset(queryset)
    queryset = queryset.filter(tags__name__regex='三分_event')
    return queryset


def order_player(queryset):
    queryset = process_queryset(queryset)
    result = {}
    for q in queryset:
        meta = json.loads(q.meta)
        player = meta['score_player']
        score = meta['score']
        if not player:
            continue

        score += result.get(player, 0)
        result[player] = score
    result = sorted(result.items(), key=lambda x:-x[1])
    return result

def score_sum(queryset):
    queryset = queryset.distinct()
    score = 0
    for e in queryset:
        score += json.loads(e.meta).get('score', 0)
    return score

def to_ids(qs):
    return sorted([str(q.id) for q in qs])

def split_by_team(qs):
    teams = {}
    for q in qs:
        meta = json.loads(q.meta)
        score_team = meta['score_team']
        data = teams.get(score_team, [])
        data.append(q)
        teams[score_team] = data
    return teams

from datetime import datetime
def test_batch(vid):
    st = datetime.now()
    pool = Pool(processes=4)
    v = Video.objects.get(pk=vid)
    meta = json.loads(v.meta)
    m3u8 = v.m3u8
    image_template = m3u8.preview_image_template
    indexs = range(0, round(int(m3u8.duration//2)))
    ins = [image_template.format(i) for i in indexs]
    data = pool.map(cba.predict, ins)
    result = zip(indexs, data)
    print(datetime.now() - st)
    meta['logs'] = result
    v.meta = json.dumps(meeta)
    v.save()


def rm(vid):
    v = Video.objects.get(pk=vid)
    VideoScene.objects.filter(video=v).delete()
    meta = json.loads(v.meta)
    del meta['matcheds']
    del meta['processed_sections']
    v.meta = json.dumps(meta)
    v.save()

@app.task
def sync_collections(ids):
    with transaction.atomic():
        inits = Collection.objects.filter(id__in =ids)
        inits.update(status='wait')

    for c in inits:
        print(c)
        try:
            resp = c.sync()
            c.status = 'done'
            if resp.status_code not in [200, 201]:
                print(resp.content)
                raise Exception('error resp ')
        except Exception as e:
            traceback.print_exc()
            c.status = 'fail'
        finally:
            c.save()
