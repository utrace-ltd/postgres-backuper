FROM alpine:latest

WORKDIR /opt/python_backuper

RUN apk --no-cache add postgresql-client python3 py3-pip

COPY requirements.txt ./

RUN pip3 install --no-cache-dir -r requirements.txt

COPY python_pg_backuper.py ./

ENV VAULT_ADDR='https://vault.example.com'
ENV VAULT_LOGIN='your_vault_login'
ENV VAULT_PASSWORD='your_vault_password'
ENV PATH_TO_SECRETS='your_path_to_secrets'
ENV PATH_TO_SECRETS2='your_path_to_secrets'
ENV PATH_TO_SECRETS3='your_path_to_secrets'
ENV PATH_TO_SECRETS4='your_path_to_secrets'
ENV BACKUP_ONLY='prod_or_other_or_all'
ENV AWS_ACCESS_KEY_ID='your_access_key_for_aws'
ENV AWS_SECRET_ACCESS_KEY='your_secret_access_key_for_aws'
ENV AWS_BUCKET_NAME='your_aws_bucket_name'
ENV AWS_STORAGE_URL='s3-storage.example.com'

CMD [ "python", "python_pg_backuper.py" ]
