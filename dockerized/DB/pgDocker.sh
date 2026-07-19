#!/bin/bash
#Author: skondla@me.com , Date: 05/10/2023
#Purpose: Create PostgreSQL database for Python Flask Web Applications
export PGPASSFILE=~/.pgpass
docker run -d -p 6432:5432 -e LANG=de_DE.utf8 -e POSTGRES_INITDB_ARGS="--locale-provider=icu --icu-locale=de-DE" -e POSTGRES_PASSWORD=mysecretpassword postgres:15-alpine 

#example - connect to 
#export PGPASSFILE=~/.pgpass
#psql -h localhost -U skondla flaskapp -p 6432

#psql -h localhost -U postgres postgres -p 6432

#psql -h localhost -U postgres postgres -p 5432

#psql -h localhost -U skondla flaskapp -p 5432
#flaskapp=# \conninfo
#You are connected to database "flaskapp" as user "skondla" on host "localhost" (address "::1") at port "5432".

#psql postgresql://skondla:skondla_flaskapp_db_password@localhost:5432/flaskapp

#Schema 

# psql -h localhost -U postgres postgres -p 6432 -f ../ADMIN/schema/flaskapp.sql
