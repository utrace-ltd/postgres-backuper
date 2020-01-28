FROM python:3

WORKDIR /opt/python_backuper

RUN python -m pip install --upgrade pip
RUN apt update && apt install -y postgresql-client

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY python_pg_backuper.py ./

ENV VAULT_ADDR='https://vault.example.com'
ENV VAULT_SECRET='yor_vault_secret'
ENV PATH_TO_SECRETS='your_path_to_secrets'
ENV AWS_ACCESS_KEY_ID='your_access_key_for_aws'
ENV AWS_SECRET_ACCESS_KEY='your_secret_access_key_for_aws'
ENV AWS_BUCKET_NAME='your_aws_bucket_name'
ENV AWS_STORAGE_URL='s3-storage.example.com'
ENV AWS_AUTH_REGION_NAME='example-region'

CMD [ "python", "python_pg_backuper.py" ]
