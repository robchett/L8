#!/bin/bash

python setup.py install

function create_service() {
	echo "Creating service $1"
	touch /etc/systemd/system/$1.service
	chmod 664 /etc/systemd/system/$1.service
	cat << SERVICE > /etc/systemd/system/$1.service
[Unit]
Description=$1
After=network.target redis.service mariadb.service

[Service]
ExecStart=/usr/bin/python $2/$1.py
Type=simple

[Install]
WantedBy=default.target
SERVICE
}

create_service s8 `pwd`

create_service a8 `pwd`

create_service p8 `pwd`
