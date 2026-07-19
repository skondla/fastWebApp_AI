#!/bin/bash
#Author: skondla@me.com
#Purpose: List Unique instance class for all engines

rm -f rdsInstClasses.lst
/usr/local/bin/aws rds describe-db-engine-versions \
 | grep Engine | \
 egrep -v '(DBEngineDescription|EngineVersion|DBEngineVersionDescription)' | \
 egrep '(aurora|postgres|mysql)'|  awk '{print $2}' | sort -rn | uniq | cut -f2 -d'"' > getEngines.lst

for engine in `cat getEngines.lst | awk '{print $1}'` 
do

 /usr/local/bin/aws rds describe-orderable-db-instance-options --engine engine --query OrderableDBInstanceOptions[*].DBInstanceClass \
  --output text | sed -e 'y/\t/\n/' |  egrep -v '(db.r3|db.r4|db.m3|db.m4|24x|16x|12x)' |sort -rn|uniq >> rdsInstClasses.lst
  #--output text | sed -e 'y/\t/\n/' |  egrep -v '(db.r3|db.r4|db.t2|db.m3|db.m4|24x|16x|12x)' |sort -rn|uniq >> rdsInstClasses.lst
done

cat rdsInstClasses.lst | sort -rn | uniq > rdsInstClasses.sorted
