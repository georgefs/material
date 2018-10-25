from django.core.management.base import BaseCommand, CommandError
from cba import players, teams
from cba.models import Player, Team, Action
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

class Command(BaseCommand):
    help = 'load cba fixture'

    def handle(self, *args, **options):
        for team_name, player_names in teams.teams.items():
            team, _ = Team.objects.get_or_create(name=team_name)
            for player_name in player_names:
                try:
                    player_nick_names = players.players[player_name]
                except:
                    print(player_name)
                    continue

                player, _ = Player.objects.get_or_create(team=team, name=player_name)
                player.nick_names = player_nick_names
                player.save()
        for action_name, keywords in actions.items():
            action, _ = Action.objects.get_or_create(name=action_name)
            action.keywords = keywords
            action.save()

