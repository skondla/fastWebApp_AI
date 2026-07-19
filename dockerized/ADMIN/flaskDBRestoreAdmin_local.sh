#!/bin/bash
#Author: skondla@me.com , Date: 10/21/2019
#Purpose: Admin interface for restoring database from snapshot using flask web framework & dB authentication
CURR_DIR=`pwd`
export FLASK_APP=${CURR_DIR}/__init__.py
export FLASK_ENV=ADMIN
export FLASK_DEBUG=1
export shost=localhost
export sport=5432
export suser=skondla
export spassword=skondla_flaskapp_db_password
export sdatabase=flaskapp
export region=us-east-1

flask run -h localhost -p 30443 --with-threads \
 --cert ./certs/certificate.pem \
 --key ./certs/key.pem --debugger > flask_admin.log 

 #--cert /etc/ssl/certs/star_clearleap_com-expires-2021-07.crt \
