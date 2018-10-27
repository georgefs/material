from .models import Live, Action, Player, Team
from material.models import Video, VideoScene, Tag, Collection
from cba.models import Player
import logging
import json
from . import video_helper
from collections import Counter
from material import cba
import requests
logger = logging.getLogger(__name__)


def extract_score_message(event):
    score_team = event['score_team']
    messages = event['messages']

    raw_message = "\n".join(messages)
    logger.info('----extract score message---')
    players = Player.extract(raw_message, [score_team])
    logger.info('----players-----')
    logger.info(players)
    logger.info('----score_player----')
    score_player = None
    score_player = players and players[-1][1] or None
    logger.info('----actions-----')
    actions = Action.extract("\n".join(event['messages'][-2:]))
    action = actions and actions[-1][1] or None
    logger.info(actions)
    logger.info('----extract score message---\n\n')

    event['score_player'] = score_player
    event['action'] = action
    event['messages'] = raw_message
    
    return event


def live_events(live_id):
    for event in Live.live_events(live_id):
        if event['type'] == 'score':
            yield extract_score_message(event)
        if event['type'] == 'change_section':
            yield event

                
def tagger(video_id, video_end=False):
    video = Video.objects.get(pk=video_id)

    meta = json.loads(video.meta)
    logs = meta.get('logs', [])
    live_id = meta['live_id']
    team1 = meta['home_team']
    team2 = meta['away_team']
    matched = meta.get('matched', {})

    time_mapping = dict(logs)

    # scene log score
    for scene, preview_url in video.scene_previews:
        scene_idx = scene['idx']
        if scene_idx in time_mapping.keys():
            continue
        else:
            time_mapping[scene_idx] = video_helper.predict(preview_url)

    logs = [v for v in time_mapping.items()]
        
    point_counter = Counter([tuple(v) for v in time_mapping.values() if v])
    point_frame = [l[0] for l in logs if l[1]]
    none_point_range = [v for v in zip(point_frame, point_frame[1:]) if v[1] - v[0] > 4]
    score_mappings = dict(sorted([(tuple(l[1]), {"time": int(l[0])*2}) for l in time_mapping.items() if l[1]], key=lambda x:-x[1]['time']))

    change_sections = []
    for live_event in live_events(live_id):
        if live_event['type'] == 'score':
            key = tuple([str(v) for v in live_event['point']])
            try:
                score_mappings[key]['event'] = live_event
            except Exception as e:
                logger.warning("point is not match {}".format(key))
        elif live_event['type'] == 'change_section':
            change_sections.append(live_event)

    point_infos = [v for v in sorted(score_mappings.items(), key=lambda x:x[1]['time'])]

    old_point = (0, 0)
    section = 1
    flag = False
    for idx in range(len(point_infos)):
        point, info = point_infos[idx]
        event_meta = {}
        event_meta['score_team'] = None
        event_meta['score_player'] = None
        event_meta['score'] = 0
        if point_counter.get(point, 0) < 4:
            flag = True
            continue
        try:
            p_n = [int(p) for p in point_infos[idx+1][0]]
            if flag:
                p_p = [int(p) for p in point_infos[idx-2][0]]
            else:
                p_p = [int(p) for p in point_infos[idx-1][0]]

            p = [int(p) for p in point]
            if not (4 > (sum(p_n) - sum(p)) > 0 or 4 > (sum(p) - sum(p_p)) > 0):
                flag = True
                continue
            flag = False
        except Exception as e:
            pass
        
        event = info.get('event', {})
        try:
            p0, p1 = int(point[0]) - int(old_point[0]), int(point[1]) - int(old_point[1])
        except Exception as e:
            logger.warning("point cacular error {} {} by {}".format(point, old_point, e))
        finally:
            old_point = point
        point_change_time = info['time']
        msg = event.get('messages', "")
        section = event.get('section', section)
        section = section > 4 and 4 or section
        tags = []
        section_tag, _ = Tag.objects.get_or_create(name="section_{}".format(section))
        tags.append(section_tag)
        score_action = ""
        event_meta['section'] = section
        
        if bool(p0) ^ bool(p1):
            score = p0 or p1
            score_action = None

            if score == 1:
                score_action = "罚球" 
            elif score == 3:
                score_action = "三分"
            else:
                score_action = event.get('action')
                if score_action:
                    score_action = score_action.name
                else:
                    score_action = "其他事件"

            event_tag, _ = Tag.objects.get_or_create(name="{}_event".format(score_action))
            tags.append(event_tag)

            score_player = event.get('score_player', None)
            if score_player:
                score_player_tag, _ = Tag.objects.get_or_create(name="{}_score_player".format(score_player.name))
                tags.append(score_player_tag)
                event_meta['score_player'] = score_player.name
                event_meta['score'] = score

            if p0 and p1:
                score_team = None
            elif p0:
                score_team = team1
            else:
                score_team = team2
            if score_team:
                score_team_tag, _ = Tag.objects.get_or_create(name="{}_score_team".format(score_team))
                tags.append(score_team_tag)
            event_meta['score_team'] = score_team


        match_key = json.dumps(point)
        videoscene_id = matched.get(match_key, None)

        msg = "[{}:{}]{}".format(point[0], point[1], msg)
        event_meta = json.dumps(event_meta)
        if not videoscene_id:
            videoscene = VideoScene()
        else:
            videoscene = VideoScene.objects.get(pk=videoscene_id)

        videoscene.text = msg
        videoscene.video = video
        videoscene.end = point_change_time 
        videoscene.meta = event_meta
        if score_action == '罚球':
            videoscene.start = point_change_time - 29
        else:
            videoscene.start = point_change_time - 5
        videoscene.save()

        tag, _ = Tag.objects.get_or_create(name="new")
        tags.append(tag)
        videoscene.tags.add(*tags)

        matched[match_key] = videoscene.id

    for change_section_event in change_sections:
        if change_section_event['section'] not in [2, 3, 4]:
            continue
        print(video.id, change_section_event['section'] - 1, change_section_event['point'])
        create_collections(video.id, change_section_event['section'] - 1, change_section_event['point'])

    if video_end:
        create_collections(video.id, 4, point)

    meta['matched'] = matched
    meta['logs'] = logs
    video.meta = json.dumps(meta)
    video.save()


def process_queryset(qs):
    scene_ids = set([s.id for s in qs])
    scenes = VideoScene.objects.filter(id__in=scene_ids)
    return scenes

def create_collections(vid, section, point=None):
    v = Video.objects.get(pk=vid)
    queryset = VideoScene.objects.filter(video=v).select_related()
    meta = json.loads(v.meta)
    home_team = meta['home_team']
    away_team = meta['away_team']
    live_id = meta['live_id']
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

    def three_point_collection(queryset, section_name, split=True):
        queryset = query_three_point(queryset)
        if split:
            team_info = split_by_team(queryset)
        else:
            team_info = {"": queryset}

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
        summary = Live.summary(live_id)
        for team, scenes in teams.items():
            team_queryset = process_queryset(scenes)
            player_scores = order_player(team_queryset)
            stars = []
            ps = []
            for player, score in player_scores:
                try:
                    player_obj = Player.objects.get(team__name=team, name=player)
                except:
                    continue


                if player_obj.is_star:
                    stars.append(player)
                else:
                    ps.append(player)
            c = 0
            for player in (stars + ps):
                if c >= 2:
                    break
                ct = ""
                if team == home_team:
                    ct = "team1"
                elif team == away_team:
                    ct = "team2"

                player_summary = summary.get(ct, {}).get(player, None)
                if player_summary:
                    P = player_summary['PTS']
                    RB = int(player_summary['OR']) + int(player_summary['RB'])
                    AST = player_summary['AST']
                    summary_text = " {}分 {}籃板 {}助攻".format(P, RB, AST)
                else:
                    summary_text = ""
                team_queryset = team_queryset.exclude(tags__name='罚球_event').exclude(tags__name='unsafe')
                if not team_queryset:
                    continue
                score_scenes = query_tag(team_queryset, "{}_score_player".format(player))
                ids = to_ids(score_scenes)

                tags = ["CBA","篮球", home_team, away_team,"人名","精彩","集锦"]
                events = extract_events(score_scenes)
                tags += events

                name = "【{}{}集锦】 {}".format(player, summary_text, suffix)
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
    try:
        section_name = section_mapping[section]
    except:
        logger.error("error: sectio {} out of range".format(section))
        return
    section_scenes = queryset.filter(tags__name='section_{}'.format(section))

    section_highlight = highlight_collection(section_scenes, section_name)
    section_three_point = three_point_collection(section_scenes, section_name, False)

    if section == "2":
        half_scenes = queryset.filter(tags__name__regex='section_[12]')
        section_name = "上半场"
        half_highlight = highlight_collection(half_scenes, section_name, 13)
        half_three_point = three_point_collection(half_scenes, section_name)
        half_score_king = score_king_collection(half_scenes, section_name)

    if section == "4":
        full_scenes = queryset
        section_name = "全场"
        full_highlight = highlight_collection(full_scenes, section_name, 20)
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
        try:
            score_team = meta['score_team']
        except:
            import pdb;pdb.set_trace()
        if not score_team:
            continue
        data = teams.get(score_team, [])
        data.append(q)
        teams[score_team] = data
    return teams

