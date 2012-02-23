from sqlalchemy.schema import *
from sqlalchemy.types import *
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import synonym_for

from gamelion.model.meta import Base

class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, nullable=False, primary_key=True)
    name = Column(String(128), nullable=False)

tag_map = Table(
    "tag_map", 
    Base.metadata,
    Column(
        "server_id", 
        Integer,
        ForeignKey("servers.id", ondelete="CASCADE")
        #primary_key=True
    ),
    Column(
        "tag_id",
        Integer,
        ForeignKey("tags.id")
        #primary_key=True
    )
)

class Server(Base):
    __tablename__ = "servers"

    id = Column(Integer, Sequence("server_id_seq"), unique=True) 
    address = Column(String(15), primary_key=True, nullable=False)
    port = Column(Integer, primary_key=True, nullable=False)
    name = Column(String(256, convert_unicode=True), nullable=True)
    app_id = Column(Integer, ForeignKey("games.id"), nullable=True)
    map = Column(String(64, convert_unicode=True), nullable=True)
    number_of_players = Column(Integer, nullable=True)
    max_players = Column(Integer, nullable=True)
    number_of_bots = Column(Integer, nullable=True)
    is_dedicated = Column(String(1), nullable=True)
    operating_system = Column(String(1), nullable=True)
    password_required = Column(Boolean, nullable=True)
    is_secure = Column(Boolean, nullable=True)
    version = Column(String(64, convert_unicode=True), nullable=True)
    timeouts = Column(Integer, default=0)
    timestamp = Column(DateTime, nullable=False)
    hotness_this_month = Column(Float, server_default='0', default=0)
    number_of_hotness_this_month = Column(
        Integer, 
        nullable=False, 
        #server_default='0',
        default=0
    )
    hotness_all_time = Column(Float, server_default='0', default=0)
    number_of_hotness_all_time = Column(
        Integer, 
        nullable=False, 
        server_default='0',
        default=0
    )
    
    tags = relationship(
        "Tag",
        secondary=tag_map,
        cascade="all",
        passive_deletes=True,
        backref="servers",
        lazy="subquery"
    )

    game = relationship(
        Game, 
        cascade="save-update, merge", 
        lazy="subquery"
    )


    @synonym_for('tags')
    @property
    def tags_str(self):
        return [str(t) for t in self.tags]

    @synonym_for('game')
    @property
    def app_name(self):
        if self.game == None:
            return None
        else:
            return self.game.name

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

class Tag(Base):
    __tablename__= "tags"

    def __init__(self, name):
        super(Base, self).__init__()
        self.name = name

    def __str__(self):
        return self.name
    
    id = Column(Integer, Sequence("tag_id_seq"), unique=True)
    name = Column(
        String(256, convert_unicode=True), 
        nullable=False, 
        index=True, 
        primary_key=True
    )

