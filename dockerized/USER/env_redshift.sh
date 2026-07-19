#source database 
shost=iottelemtry.cluster-a1sd3rst23.us-east-1.rds.amazonaws.com
sport=5432
sdatabase=flaskapp
suser=skondla
spassword=iot_telemtry_skondla_db_password
region=us-east-1
#target database
thost=iotedw.a1sd3rst23.us-east-1.redshift.amazonaws.com
tport=5439
tdatabase=iotdb
tuser=skondla
tpassword=iot_skondla_iotdb_db_password