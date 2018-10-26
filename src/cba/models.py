from django.db import models
from datetime import datetime
import json
import logging
import pytz
import requests
from django.db import transaction

logger = logging.getLogger(__name__)
# Create your models here.

class Team(models.Model):
    name = models.CharField(max_length=1024, unique=True)


    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.name

    class Meta:
        indexes = [
            models.Index(fields=['name']),
        ]

class Player(models.Model):
    name = models.CharField(max_length=1024)
    _nick_names = models.TextField()
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    is_star = models.BooleanField(default=False)


    def __unicode__(self):
        return "【{}】{}".format(self.team, self.name)

    def __str__(self):
        return "【{}】{}".format(self.team, self.name)

    class Meta:
        unique_together = ('team', 'name')
        indexes = [
            models.Index(fields=['team']),
        ]

    @property
    def nick_names(self):
        return [name.strip() for name in self._nick_names.split(',')]

    @nick_names.setter
    def nick_names(self, values):
        self._nick_names = ",".join(values)

    @classmethod
    def extract(cls, msg, team_names):
        live_players = cls.objects.all()
        if team_names:
            teams = Team.objects.filter(name__in=team_names)
            live_players = live_players.filter(team__in=teams)

        live_players.select_related()

        result = []
        for player in live_players:
            for player_nick_name in player.nick_names:
                pos = msg.rfind(player_nick_name)
                if pos != -1:
                    result.append((pos, player))

        return sorted(result, key=lambda x:x[0])

class Action(models.Model):
    name = models.CharField(max_length=1024, unique=True)
    _keywords = models.TextField()


    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.name

    class Meta:
        indexes = [
            models.Index(fields=['name'])
        ]

    @property
    def keywords(self):
        return [keyword.strip() for keyword in self._keywords.strip(',')]

    @keywords.setter
    def keywords(self, values):
        self._keywords = ",".join(values)

    @classmethod
    def extract(cls, msg):
        actions = cls.objects.all()

        result = []
        for action in actions:
            for keyword in action.keywords:
                pos = msg.rfind(keyword)
                if pos != -1:
                    result.append((pos, action))
        logger.info("action extract {}")
        return result


class Live(models.Model):
    live_id = models.CharField(max_length=1024, unique=True)
    _messages = models.TextField(default="[]")
    updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.live_id

    def __str__(self):
        return self.live_id

    @property
    def messages(self):
        messages = json.loads(self._messages)
        if (datetime.utcnow().replace(tzinfo=pytz.utc) - self.updated).total_seconds() > 10:
            self.update_messages(messages)
        return reversed(messages)

    @messages.setter
    def messages(self, values):
        self._messages = json.dumps(values)

    def update_messages(self, old_messages, save=True):
        t = datetime.now().strftime('%s000')
        api = 'http://api.sports.sina.com.cn/?p=live&s=livecast&a=livecastlogv3&format=json&key=l_{}&id={}&order=-1&num=10000&year=2014-03-05&callback=&dpc=1'

        fetch_message_id = ""
        original_top_message = old_messages and old_messages[0] or {"id": None}
        new_messages = []
        end = False
        while True:
            messages = []
            try:
                url = api.format(self.live_id, fetch_message_id)
                logger.warning(url)
                resp = requests.get(url)
                messages = resp.json()['result']['data']

                for message in messages:
                    if message['id'] == original_top_message['id']:
                        end = True
                        logger.warning(fetch_message_id)
                        break
                    else:
                        new_messages.append(message)
                        fetch_message_id = message['id']
            except Exception as e:
                logger.warning('request api error {}'.format(url))
                return

            if end or not messages:
                break

        messages = new_messages + old_messages
        self._messages = json.dumps(messages)
        print(len(messages))
        if save:
            self.save()
        
    
    @classmethod
    def live_message(cls, live_id):
        live, _ = cls.objects.get_or_create(live_id=live_id)
        if _:
            live.update_messages([])
        for message in live.messages:
            yield message

    @classmethod
    def live_events(cls, live_id):
        messages = cls.live_message(live_id)

        point_mappings = {}
        tmp = []
        old_point = (0, 0)
        old_section = 0
        for message in messages:
            # material message
            try:
                point = (int(message['s']['s1']), int(message['s']['s2']))
                team1 = message['team1']
                team2 = message['team2']
            except:
                continue

            #  live message
            base = {}
            base['team1'] = team1
            base['team2'] = team2
            base['section'] = message['q']
            base['point'] = point

            ## point event
            tmp.append(message['m'].strip())
            if point != old_point:
                info = {}
                info['type'] = "score"
                info['messages'] = tmp

                if point[0] != old_point[0]:
                    info['score_team'] = base["team1"]
                    info['score_point'] = point[0] - old_point[0]
                else:
                    info['score_team'] = base["team2"]
                    info['score_point'] = point[1] - old_point[1]

                tmp = []
                info.update(base)
                old_point = point
                yield info

            ## change section
            if old_section != base['section']:
                info = {}
                info['type'] = "change_section"
                info.update(base)
                old_section = base['section']
                yield info
