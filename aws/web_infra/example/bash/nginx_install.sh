#!/bin/bash 
yum update –y 
#amazon-linux-extras install nginx1.12
yum install -y nginx
nginx -v
systemctl start nginx
systemctl enable nginx
chmod 2775 /usr/share/nginx/html 
find /usr/share/nginx/html -type d -exec chmod 2775 {} \;
find /usr/share/nginx/html -type f -exec chmod 0664 {} \;
echo "<h3 style=\"color:green;\"> Welcome to my NGINX web server! User data instillation was a SUCCESS! </h3>" > /usr/share/nginx/html/index.html
echo "<h1 Hello Sudheer Kondla @Data Cube inc from $(hostname -f) </h1>" >> /usr/share/nginx/html/index.html
echo "<h3> Hello Sudheer Kondla @Data Cube inc from $(hostname -f) </h3>" >> /usr/share/nginx/html/index.html
echo "<h1> Hello Sudheer Kondla @Data Cube inc from $(hostname -f) </h1>" >> /usr/share/nginx/html/index.html
echo "<h2 style=\"color:blue;\"> Hello Sudheer Kondla @Data Cube inc from $(hostname -f) </h2>" >> /usr/share/nginx/html/index.html
echo "<h2 style=\"color:Tomato;\"> This works, $(nginx -v) </h2>" >> /usr/share/nginx/html/index.html