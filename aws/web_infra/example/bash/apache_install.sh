#!/bin/bash
yum update -y
yum install -y httpd
systemctl start httpd
systemctl enable httpd
echo "<h3 style=\"color:green;\"> Welcome to my Apache web server! User data instillation was a SUCCESS! </h3>" > /var/www/html/index.html
echo "<h1> Hello Sudheer Kondla @Data Cube inc from $(hostname -f) </h1>”>> /var/www/html/index.html
echo "<h1 style=\"color:Tomato;\”> This works,  $(httpd -v) </h1>" >>  /var/www/html/index.html
echo "<h2 style=\"color:blue;\"> Hello Sudheer Kondla @Data Cube inc from $(hostname -f) </h2>" >>  /var/www/html/index.html
echo "<h2 style=\"color:blue;\"> Hello Sudheer Kondla @Data Cube inc from $(hostname -f) </h2>" >>  /var/www/html/index.html