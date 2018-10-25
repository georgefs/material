from django.contrib import admin
from cba.models import Player, Team, Action, Live

# Register your models here.

class PlayerAdmin(admin.ModelAdmin):
    list_display = ['name',  '_nick_names']
    list_editable = ["_nick_names"]

class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', ]

class ActionAdmin(admin.ModelAdmin):
    list_display = ['name', "_keywords"]
    list_editable = ["_keywords"]

class LiveAdmin(admin.ModelAdmin):
    list_display = ['live_id', ]


admin.site.register(Player, PlayerAdmin)
admin.site.register(Team, TeamAdmin)
admin.site.register(Action, ActionAdmin)
admin.site.register(Live, LiveAdmin)
