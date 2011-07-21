from formencode import Schema
from formencode.variabledecode import NestedVariables
from formencode.validators import *
from formencode.foreach import ForEach

NUM_PRIMARY_CHECK_BOXES = 3

class AppID(object):
    def __init__(self, app_id, app_name):
        self.app_id = app_id
        self.app_name = app_name

_apps = [
    AppID(240, 'Counter-Strike: Source'),
    AppID(440, 'Team Fortress 2'),
    AppID(10, 'Counter-Strike'),
    AppID(70, 'Half-Life'),
    AppID(1250, 'Killing Floor'),
    AppID(17580, 'Dystopia'),
    AppID(31206, 'Total War: Shogun 2'),
    AppID(550, 'Left 4 Dead 2'), 
    AppID(300, 'Day of Defeat: Source'), 
]

_server_options = [
        'Map',
        'Anti-cheat',
        'Server not full',
        'Has users playing',
        'Is not password protected',
    ]

def get_searchable_apps():
    return _apps

def get_searchable_server_options():
    return _server_options

class SearchForm(Schema):
    pre_validators = [NestedVariables()]
    search = String()
    game = ForEach(Int(), 
                   OneOf([app.app_id for app in get_searchable_apps()]))
    ignore_key_missing = True
    allow_extra_fields = True

