from .models import Live, Action, Player, Team
from material.models import Video, VideoScene, Tag
import logging
import json
from cba import helpers
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
    logger.info(actions)
    logger.info('----extract score message---\n\n')

    event['score_player'] = score_player
    actions = actions and actions[-1] or None
    event['messages'] = raw_message
    
    return event


def live_events(live_id):
    for event in Live.live_events(live_id):
        if event['type'] == 'score':
            yield extract_score_message(event)
        if event['type'] == 'change_section':
            yield event

                
def tagger(video):
    meta = json.loads(video.meta)
    logs = dict(meta.get('logs', []))
    live_id = meta['live_id']
    team1 = meta['home_team']
    team2 = meta['away_team']

    # scene log score
    for scene, preview_url in video.scene_previews:
        scene_idx = scene['idx']
        if logs.get(scene_idx):
            continue
        else:
            logs[scene_idx] = helpers.predict(preview_url)

    score_mappings = dict(sorted([(tuple(l[1]), l[0]) for l in logs.items() if l[1]], key=lambda x:-x[1]))


    passed_sections = []
    for live_event in live_events(live_id):
        if live_event['type'] == 'score':
            print(live_event)
            pass
        elif live_event['type'] == 'change_section':
            pass

