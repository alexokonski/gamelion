#!/bin/bash

for i in {4..10}
do
    CONSUMER_DIR=~/gamelion/srv/consumer${i}
    if [ ! -d "$CONSUMER_DIR" ]; then
        setuidgid alex cp -R template/ ~/gamelion/srv/consumer${i}
        ln -s ~/gamelion/srv/consumer${i} /etc/service/consumer${i}
    fi
done
