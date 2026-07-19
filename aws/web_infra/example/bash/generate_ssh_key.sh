# aws ec2 create-key-pair \
#     --key-name my-key-pair \
#     --key-type rsa \
#     --key-format pem \
#     --query "KeyMaterial" \
#     --output text > ssh-key1-us-east-2.pem

aws ec2 create-key-pair --key-name ssh-key1-us-east-2 --query 'KeyMaterial' --output text > ssh-key1-us-east-2.pem
chmod 0400 ssh-key1-us-east-2.pem
ssh-keygen -y -f ssh-key1-us-east-2.pem > ssh-key1-us-east-2.pub
aws ec2 import-key-pair --key-name ssh-key1-us-east-2-1 --public-key-material fileb://ssh-key1-us-east-2.pub --region us-east-2