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
    map = Column(String(64), nullable=True)
    number_of_players = Column(Integer, nullable=True)
    max_players = Column(Integer, nullable=True)
    number_of_bots = Column(Integer, nullable=True)
    is_dedicated = Column(String(1), nullable=True)
    operating_system = Column(String(1), nullable=True)
    password_required = Column(Boolean, nullable=True)
    is_secure = Column(Boolean, nullable=True)
    version = Column(String(64), nullable=True)
    _game = relation(Game)

    @synonym_for('_game')
    @property
    def app_name(self):
        if self._game == None:
            return None
        else:
            return self._game.name

    @synonym_for('is_secure')
    @property
    def is_secure_str(self):
        if self.is_secure:
            return 'Yes'
        else:
            return 'No'

    @synonym_for('password_required')
    @property 
    def password_required_str(self):
        if self.password_required:
            return 'Yes'
        else:
            return 'No'

    @synonym_for('operating_system')
    @property
    def operating_system_str(self):
        if self.operating_system == 'l':
            return 'Linux'
        elif self.operating_system == 'w':
            return 'Windows'
        else:
            return '?'

