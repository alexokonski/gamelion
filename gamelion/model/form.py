from formencode import Schema
from formencode.variabledecode import NestedVariables
from formencode.validators import *
from formencode.foreach import ForEach

from gamelion.model import *

class Checkbox(object):
    def __init__(self, name='', label='', value=1):
        self.name = name
        self.value = value
        self.label = label

    def apply_filter(self, query):
        raise NotImplementedError

class CheckboxGroup(object):
    def __init__(self, label, checkboxes, number_initially_visible=4):
        self.label = label
        self.checkboxes = checkboxes
        self.number_initially_visible = number_initially_visible

    def get_checkboxes(self):
        return self.checkboxes

    def get_matching_checkboxes(self, request_params):
        return [c for c in self.checkboxes if c.name in request_params]

    def get_number_initially_visible(self):
        return self.number_initially_visible

    def apply_filter(self, query, request_params):
        raise NotImplementedError 

class AppIDCheckbox(Checkbox):
    def __init__(self, name='', label='', app_id=0, value=1):
        super(AppIDCheckbox, self).__init__(name, label, value)
        self.app_id = app_id

class AppIDCheckboxGroup(CheckboxGroup):
    def apply_filter(self, query, request_params):
        app_ids = [app.app_id for app in self.checkboxes \
                   if app.name in request_params]
        
        if len(app_ids) == 0:
            app_ids = [app.app_id for app in self.checkboxes]
            
        return query.filter(Server.app_id.in_(app_ids))

class ServerOptionCheckbox(Checkbox):
    def __init__(self, name='', label='', condition=None, value=1):
        super(ServerOptionCheckbox, self).__init__(
            name=name,
            label=label,
            value=value
        )
        self.condition = condition

    def apply_filter(self, query):
        return query.filter(self.condition)

class ServerOptionCheckboxGroup(CheckboxGroup):
    def apply_filter(self, query, request_params):
        options = [option for option in self.checkboxes \
                   if option.name in request_params]

        for option in options:
            query = option.apply_filter(query)

        return query

_apps = [
    AppIDCheckbox(name='css', app_id=240, label='Counter-Strike: Source'),
    AppIDCheckbox(name='tf2', app_id=440, label='Team Fortress 2'),
    AppIDCheckbox(name='cs', app_id=10, label='Counter-Strike'),
    AppIDCheckbox(name='mw3', app_id=-22846, label='CoD: Modern Warfare 3'),
    AppIDCheckbox(name='l4d2', app_id=550, label='Left 4 Dead 2'), 
    AppIDCheckbox(name='gm', app_id=4000, label='Garry\'s Mod'),
    AppIDCheckbox(name='hl', app_id=70, label='Half-Life'),
    AppIDCheckbox(name='kf', app_id=1250, label='Killing Floor'),
    AppIDCheckbox(name='dys', app_id=17580, label='Dystopia'),
    AppIDCheckbox(name='tws2', app_id=31206, label='Total War: Shogun 2'),
    AppIDCheckbox(name='dods', app_id=300, label='Day of Defeat: Source'), 
]

_server_options = [
    ServerOptionCheckbox(
        name='vac', 
        label='Anti-cheat', 
        condition=(Server.is_secure == True),
    ),
    ServerOptionCheckbox(
        name='not_full', 
        label='Server not full',
        condition=(Server.number_of_players < Server.max_players)
    ),
    ServerOptionCheckbox(
        name='not_empty', 
        label='Has users playing',
        condition=(Server.number_of_players > 0)
    ),
    ServerOptionCheckbox(
        name='no_password', 
        label='Is not password protected',
        condition=(Server.password_required == False)
    )
]

_groups = [
    AppIDCheckboxGroup('Games', _apps),
    ServerOptionCheckboxGroup('Server Options', _server_options),
]

def get_checkbox_groups():
    return _groups

class SearchForm(Schema):
    pre_validators = [NestedVariables()]
    search = String()
    map = String()
    #game = ForEach(Int(), 
    #               OneOf([app.app_id for app in _apps]))
    css = Int(min=0, max=1)
    tf2 = Int(min=0, max=1)
    l4d2 = Int(min=0, max=1)
    gm = Int(min=0, max=1)
    cs = Int(min=0, max=1)
    hl = Int(min=0, max=1)
    kf = Int(min=0, max=1)
    dys = Int(min=0, max=1)
    tws2 = Int(min=0, max=1)
    dods = Int(min=0, max=1)
    mw3 = Int(min=0, max=1)

    vac = Int(min=0, max=1)
    not_full = Int(min=0, max=1)
    not_empty = Int(min=0, max=1)
    no_password = Int(min=0, max=1)

    ignore_key_missing = True
    allow_extra_fields = True

