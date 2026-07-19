#!/bin/bash

THRESHOLD_DAYS=90

for user in $(aws iam list-users --query 'Users[*].UserName' --output text); do
  for key_id in $(aws iam list-access-keys --user-name $user --query 'AccessKeyMetadata[*].AccessKeyId' --output text); do
    create_date=$(aws iam list-access-keys --user-name $user \
                  --query "AccessKeyMetadata[?AccessKeyId=='$key_id'].CreateDate" \
                  --output text)
    key_age=$(($(($(date +%s) - $(date -d "$create_date" +%s))) / 86400))
    if [ "$key_age" -gt "$THRESHOLD_DAYS" ]; then
      echo "Deleting key $key_id for user $user (age: $key_age days)"
      aws iam update-access-key --access-key-id $key_id --status Inactive --user-name $user
      aws iam delete-access-key --access-key-id $key_id --user-name $user
    fi
  done
done

