from paste.deploy import appconfig
from pylons import config
from gamelion.config.environment import load_environment
from gamelion.model import *
import datetime 
import time
import logging

# set up the pylons environment

conf = appconfig('config:amazon.ini', relative_to='.')
load_environment(conf.global_conf, conf.local_conf)

# delete a server if it hasn't been successfully
# pinged in this long
TIMEOUT_CUTOFF = datetime.timedelta(days=5)

def main():
    logging.basicConfig(level=logging.DEBUG)

    cutoff_date = datetime.datetime.now() - TIMEOUT_CUTOFF

    servers = Session.query(Server)\
            .filter(Server.timestamp < cutoff_date)\
            .all()

    logging.debug('DELETING %d SERVERS', len(servers))
    before_time = time.time()

    for server in servers:
        Session.delete(server)

    Session.commit()
    after_time = time.time()

    logging.debug('DELETED... TOOK %f SECONDS', after_time - before_time)

main()
