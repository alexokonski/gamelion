#!/bin/bash

for i in {1..5}
do
	BASE_NAME=`printf "consumer%02d" ${i}`
	CONSUMER_DIR=~/gamelion/srv/${BASE_NAME}
	if [ ! -d "$CONSUMER_DIR" ]; then
		setuidgid alex mkdir -p ${CONSUMER_DIR}
		setuidgid alex cp -R -t ${CONSUMER_DIR} template/* 		
		ln -s ${CONSUMER_DIR} /etc/service/${BASE_NAME}
	fi
done
