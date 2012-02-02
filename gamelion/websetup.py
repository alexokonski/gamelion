"""Setup the gamelion application"""
import logging

import pylons.test

from gamelion.config.environment import load_environment
from gamelion.model.meta import Session, Base
from gamelion.model import *

log = logging.getLogger(__name__)

def setup_app(command, conf, vars):
    """Place any commands to setup gamelion here"""
    # Don't reload the app if it was loaded under the testing environment
    if not pylons.test.pylonsapp:
        load_environment(conf.global_conf, conf.local_conf)

    # Create the tables if they don't already exist
    Base.metadata.drop_all(bind=Session.bind)
    Base.metadata.create_all(bind=Session.bind)

    game = Game()
    game.id = 440
    game.name = "Team Fortress 2"
    Session.add(game)

    game.id = -22846
    game.name = "CoD: Modern Warfare 3"
    Session.add(game)

    Session.commit()
