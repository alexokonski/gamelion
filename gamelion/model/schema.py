from sqlalchemy.schema import *
from sqlalchemy.types import *
from sqlalchemy.orm import relation
from sqlalchemy.ext.declarative import synonym_for

from gamelion.model.meta import Base

class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, nullable=False, primary_key=True)
    name = Column(String(128), nullable=False)

class Server(Base):
    __tablename__ = "servers"

    address = Column(String(15), nullable=False, primary_key=True)
    port = Column(Integer, nullable=False, primary_key=True)
    name = Column(String(256), nullable=True)
    app_id = Column(Integer, ForeignKey("games.id"), nullable=True)
    _game = relation(Game)

    @synonym_for('_game')
    @property
    def app_name(self):
        if self._game == None:
            return None
        else:
            return self._game.name

