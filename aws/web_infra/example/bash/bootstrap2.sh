#!/bin/bash 

# Update system packages
yum update -y 

# Uncomment if using Amazon Linux 2
# amazon-linux-extras enable nginx1
# yum install -y nginx

# Install Google Authenticator & Amazon SSM Agent
yum install -y google-authenticator
systemctl start amazon-ssm-agent && systemctl enable amazon-ssm-agent
# echo "auth required pam_google_authenticator.so" | tee -a /etc/pam.d/sshd
# echo "ChallengeResponseAuthentication yes" |  tee -a /etc/ssh/sshd_config
# echo "UsePAM yes" |  tee -a /etc/ssh/sshd_config
# echo "AuthenticationMethods publickey,keyboard-interactive" |  tee -a /etc/ssh/sshd_config
# sudo setenforce 0  # Temporarily disable SELinux
# systemctl restart sshd
# Install and start NGINX
yum install -y nginx
nginx -v
systemctl start nginx
systemctl enable nginx

# Set permissions for NGINX web root
chmod 2775 /usr/share/nginx/html 
find /usr/share/nginx/html -type d -exec chmod 2775 {} \;
find /usr/share/nginx/html -type f -exec chmod 0664 {} \;

# Create the index.html file with proper formatting
cat <<EOF > /usr/share/nginx/html/index.html
<!DOCTYPE html>
<html>
<head>
    <title>Welcome Page</title>s
    <style>
        h1 { color: green; }
        h2 { color: blue; }
        h3 { color: tomato; }
        #time { font-size: 1.2rem; margin-top: 10px; }
    </style>
</head>
<body>
    <h3 style="color:green;">Welcome to my NGINX web server! User data installation was a SUCCESS!</h3>
    <h1>Hello Sudheer Kondla @ Data Cube Inc from $(hostname -f)</h1>
    <h2 style="color:blue;">Uptime: $(uptime | awk '{print $1 " "  $2 " "  $3 " "  $4}')</h2>
    <h2 style="color:red;">Uptime: $(uptime)</h2>
    <h2 style="color:blue;">Hello Sudheer Kondla @ Data Cube Inc from $(hostname -f)</h2>
    <h2 style="color:Tomato;">This works, NGINX</h2>

    <h1>Current Date and Time</h1>
    <div id='time'></div>

    <script>
        function updateTime() {
            const date = new Date();
            const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
            const time = date.toLocaleTimeString();
            const day = date.toLocaleDateString(undefined, options);
            document.getElementById('time').innerHTML = \`Today is: \${day}, Current Time: \${time}\`;
        }
        setInterval(updateTime, 1000);
        updateTime();
    </script>
</body>
</html>
EOF
