"""The application's model objects"""
from gamelion.model.meta import Session, Base
from gamelion.model.schema import *
from gamelion.model.form import *

def init_model(engine):
    """Call me before using any of the tables or classes in the model"""
    Session.configure(bind=engine)
