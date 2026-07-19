#!/bin/bash
#Author: skondla@me.com , Date: 05/10/2023
#Purpose: Create Schema for Python Web Application for basic user authentication, tracking DB backup, restore requests
export PGPASSFILE=~/.pgpass
psql -d postgres -h localhost -p 6432 -U postgres -W -f ./schema/flaskapp.sql
