from paste.deploy import appconfig
from pylons import config

from gamelion.config.environment import load_environment

conf = appconfig('config:development.ini', relative_to='.')
load_environment(conf.global_conf, conf.local_conf)

from gamelion.model import *
import gamelion.lib.stringz as struct

class MasterServerQuery(object):
    def __init__(self):
        pass
