aws ec2 create-key-pair --key-name ssh-key1-us-east-2 --region us-east-2 --query 'KeyMaterial' --output text > ssh-key1-us-east-2.pem
chmod 400 ssh-key1-us-east-2.pem
ssh-keygen -y -f ssh-key1-us-east-2.pem > ssh-key1-us-east-2.pub
aws ec2 import-key-pair --key-name ssh-key1-us-east-2 --public-key-material fileb://ssh-key1-us-east-2.pub --region us-east-2



