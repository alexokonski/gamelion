#!/bin/bash -e
# based on the reddit install script (gist.github.com/922144)

GAMELION_REPO=git@github.com:hoodedmongoose/gamelion.git

set -e

source /etc/lsb-release
if [ "$DISTRIB_ID" != "Ubuntu" ]; then
	echo "ERROR: Unknown distribution $DISTRIB_ID. Only Ubuntu is supported."
	exit 1
fi


if [ $(id -u) -ne 0 ]; then
	echo "ERROR: Must be run with root privileges."
	exit 1
fi

GAMELION_USER=${SUDO_USER:-gamelion}
read -ei $GAMELION_USER -p "What user should gamelion run as? " GAMELION_USER

GAMELION_HOME=/home/$GAMELION_USER

DEBIAN_FRONTEND=noninteractive aptitude install python-dev python-mako python-formencode python-pastescript python-amqplib rabbitmq-server python-pylons git-core postgresql postgresql-client daemontools daemontools-run python-psycopg2

if ! id $GAMELION_USER > /dev/null; then
	adduser --system $GAMELION_USER
fi

echo "Installing..."
echo

if [ ! -d $GAMELION_HOME/gamelion ]; then
	sudo git clone $GAMELION_REPO
fi

# set up postgres
IS_DATABASE_CREATED=$(sudo -u postgres psql -t -c "SELECT COUNT(1) FROM pg_catalog.pg_database WHERE datname = 'gamelion';")

if [ $IS_DATABASE_CREATED -ne 1 ]; then
	cat <<PGSCRIPT | sudo -u postgres psql
CREATE DATABASE gamelion WITH ENCODING = 'utf8';
CREATE USER alex WITH PASSWORD 'password';
PGSCRIPT
fi

# set up rabbitmq
if ! rabbitmqctl list_vhosts | egrep "^/$"
then
	rabbitmqctl add_vhost /
fi

if ! rabbitmqctl list_users | egrep "^gamelion"
then
	rabbitmqctl add_user gamelion gamelion
fi

rabbitmqctl set_permissions -p / gamelion ".*" ".*" ".*"

# setup pylons
cd $GAMELION_HOME/gamelion
python setup.py develop

# setup gamelion
paster setup-app amazon.ini

if ! python -c "import kombu" 2> /dev/null
then
	easy_install kombu
fi

# setup consumer processes
if [ ! -d $GAMELION_HOME/gamelion/srv/consumer01 ]; then
	cd $GAMELION_HOME/gamelion/consumer_daemon_generate
	bash generate.sh
	cd $GAMELION_HOME
fi

ln -s ~/gamelion/srv/gamelion /etc/service/gamelion
