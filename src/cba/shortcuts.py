import live
from .models import *
import logging
import json
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
    score_player = players[-1][1]
    logger.info('----actions-----')
    actions = Action.extract("\n".joinevent['messages'][-2:]))
    logger.info(actions)
    logger.info('----extract score message---\n\n')

    event['score_player'] = score_player
    event['action'] = actions[-1]
    event['messages'] = raw_message

    return event

def live(live_id):
    for event in Live.live_events(live_id):
        if event['type'] == 'score':
            yield extract_score_message(event)
        if event['type'] == 'change_section':
            yield event

                
