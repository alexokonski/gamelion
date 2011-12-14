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

aptitude update

DEBIAN_FRONTEND=noninteractive aptitude install python-dev python-mako python-formencode python-pastescript python-amqplib rabbitmq-server python-pylons git-core postgresql postgresql-client daemontools daemontools-run python-psycopg2 nginx

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

# install kombu if needed
if ! python -c "import kombu" &> /dev/null
then
	easy_install kombu
fi

# install flup if needed
if ! python -c "import flup" &> /dev/null
then
	easy_install flup
fi

# setup consumer processes
if [ ! -d $GAMELION_HOME/gamelion/srv/consumer01 ]; then
	cd $GAMELION_HOME/gamelion/consumer_daemon_generate
	bash generate.sh
	cd $GAMELION_HOME
fi

if [ ! -L /etc/service/gamelion ]; then
	ln -s ~/gamelion/srv/gamelion /etc/service/gamelion
fi

/sbin/start svscan || true

# set up nginx
cat >/etc/nginx/sites-available/gamelion <<NGINX
server {
	listen 80;
	server_name localhost;
	
	location / {
		# host and port to fastcgi server
		fastcgi_pass 127.0.0.1:8080;
		fastcgi_param PATH_INFO \$fastcgi_script_name;
		fastcgi_param REQUEST_METHOD \$request_method;
		fastcgi_param QUERY_STRING \$query_string;
		fastcgi_param CONTENT_TYPE \$content_type;
		fastcgi_param CONTENT_LENGTH \$content_length;
		fastcgi_param SERVER_ADDR \$server_addr;
		fastcgi_param SERVER_PORT \$server_port;
		fastcgi_param SERVER_NAME \$server_name;
		fastcgi_param SERVER_PROTOCOL \$server_protocol;
		fastcgi_pass_header Authorization;
		fastcgi_intercept_errors off;
	}
	access_log	/var/log/nginx/localhost.access_log;
	error_log	/var/log/nginx/localhost.error_log;
}
NGINX

if [ ! -L /etc/nginx/sites-enabled/gamelion ]; then
	ln -s /etc/nginx/sites-available/gamelion /etc/nginx/sites-enabled/gamelion
fi

if [ -L /etc/nginx/sites-enabled/default ]; then
	# take out default server
	rm /etc/nginx/sites-enabled/default
fi

/etc/init.d/nginx restart

# install cron jobs
CRONTAB=$(mktemp)

crontab -u $GAMELION_USER -l > $CRONTAB || true

# every two hours since this may be running on a micro and 
# we can't have too many consumers...
cat >>$CRONTAB <<CRON
# m h  dom mon dow   command
0  */2  *   *   *    python $GAMELION_HOME/masterserver.py -d >> ~/masterserver.log 2>&1
CRON

crontab -u $GAMELION_USER $CRONTAB
rm $CRONTAB

echo "Installation Complete"
