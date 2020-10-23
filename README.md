# postgres-backuper

##### This script collects the database connection strings in your Vault and goes through the compiled array making backups of these databases.

##### Replace the following variable values with yours in the dockerfile and try to assemble the container. You can always get the log that the docker container gives and find out if something went wrong.

#### ENV VAULT_ADDR='https://vault.example.com'

#### ENV VAULT_SECRET='your_vault_secret'

#### ENV PATH_TO_SECRETS='your_path_to_secrets'

#### ENV PATH_TO_SECRETS2='your_path_to_secrets'

ENV PATH_TO_SECRETS2='your_path_to_secrets'

#### ENV AWS_ACCESS_KEY_ID='your_access_key_for_aws'

#### ENV AWS_SECRET_ACCESS_KEY='your_secret_access_key_for_aws'

#### ENV AWS_BUCKET_NAME='your_aws_bucket_name'

#### ENV AWS_STORAGE_URL='s3-storage.example.com'

#### ENV AWS_AUTH_REGION_NAME='example-region'
