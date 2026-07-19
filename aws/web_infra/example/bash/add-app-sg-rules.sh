aws ec2 describe-security-groups --group-ids sg-09ac16445f6ada389 --query 'SecurityGroups[*].[GroupId, IpPermissions]'
aws ec2 authorize-security-group-ingress --group-id `cat app_sg_id.sg` --protocol tcp --port 22 --cidr 10.1.7.142/32
aws ec2 authorize-security-group-egress --group-id sg-09c2bb2ef4fb0187b --protocol tcp --port 22 --cidr 10.1.1.133/32