from django.contrib import admin
from cba.models import Player, Team, Action, Live

# Register your models here.

class PlayerAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_star',  '_nick_names', 'team']
    list_editable = ["_nick_names", "is_star"]
    search_fields = ('name', '_nick_names' )
    list_filter = ['team']


class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', ]

class ActionAdmin(admin.ModelAdmin):
    search_fields = ('name', '_keywords' )
    list_display = ['name', "_keywords"]
    list_editable = ["_keywords"]

class LiveAdmin(admin.ModelAdmin):
    search_fields = ('live_id', )
    list_display = ['live_id', ]


admin.site.register(Player, PlayerAdmin)
admin.site.register(Team, TeamAdmin)
admin.site.register(Action, ActionAdmin)
admin.site.register(Live, LiveAdmin)
