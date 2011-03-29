from formencode import Schema
from formencode.variabledecode import NestedVariables
from formencode.validators import *
from formencode.foreach import ForEach

def get_primary_app_ids():
    return {
        240 : 'Counter-Strike: Source',
        440 : 'Team Fortress 2',
        10  : 'Counter-Strike'
    }

def get_secondary_app_ids():
    return {
        70    : 'Half-Life',
        17580 : 'Dystopia',
        31206 : 'Total War: Shogun 2',
        550   : 'Left 4 Dead 2', 
        300   : 'Day of Defeat: Source', 
    }

class SearchForm(Schema):
    pre_validators = [NestedVariables()]
    search = String()
    game = ForEach(Int(), 
                   OneOf(get_primary_app_ids().keys() + get_secondary_app_ids().keys()))
    ignore_key_missing = True
    allow_extra_fields = True

