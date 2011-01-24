from formencode import Schema
from formencode.variabledecode import NestedVariables
from formencode.validators import *
from formencode.foreach import ForEach

def GetValidAppIds():
    return {
        240 : 'Counter-Strike: Source',
        440 : 'Team Fortress 2',
        10  : 'Counter-Strike'
    }

class SearchForm(Schema):
    pre_validators = [NestedVariables()]
    search = String()
    game = ForEach(Int(), OneOf(GetValidAppIds().keys()))
    ignore_key_missing = True
    allow_extra_fields = True

