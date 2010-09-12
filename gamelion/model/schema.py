from sqlalchemy.schema import *
from sqlalchemy.types import *
from sqlalchemy.orm import relation

from gamelion.model.meta import Base

class Server(Base):
    __tablename__ = "servers"

    address = Column(String(15), nullable=False, primary_key=True)
    port = Column(Integer, nullable=False, primary_key=True)
