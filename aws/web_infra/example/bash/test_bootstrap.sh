# Purpose: This script is used to install and configure NGINX on an Amazon Linux instance.
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
echo "<h2 style=\"color:Tomato;\"> This works,  NGINX </h2>" >> /usr/share/nginx/html/index.html
echo "<!DOCTYPE html>
<html>

<head>
    <title>
        Date and time
    </title>
    <style>
        h1 {
            color: green;
        }

        #time {
            font-size: 1.2rem;
            margin-top: 10px;
        }
    </style>
</head>

<body>
    <h1>
        Current Date and Time
    </h1>
    <div id='time'>
    </div>
    <script>
        function updateTime() {
            const date = new Date();
            const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
            const time = date.toLocaleTimeString();
            const day = date.toLocaleDateString(undefined, options);
            document.getElementById('time').innerHTML =
                `Today is: ${day}, Current Time: ${time}`;
        }

        setInterval(updateTime, 1000);
        updateTime();
    </script>
</body>
" >> /usr/share/nginx/html/index.html