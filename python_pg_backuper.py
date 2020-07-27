# -*- coding: utf-8 -*-

import logging
import os
import re
import subprocess
import shutil
from datetime import date

import hvac
from boto.s3.connection import S3Connection
from boto.s3.key import Key

# Vault variables
VAULT_ADDR = os.environ.get("VAULT_ADDR")
VAULT_SECRET = os.environ.get("VAULT_SECRET")
PATH_TO_SECRETS = os.environ.get('PATH_TO_SECRETS')
PATH_TO_SECRETS2 = os.environ.get('PATH_TO_SECRETS2')

# Yandex S3 settings.
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_BUCKET_NAME = os.environ.get('AWS_BUCKET_NAME')
AWS_STORAGE_URL = os.environ.get('AWS_STORAGE_URL')
AWS_AUTH_REGION_NAME = os.environ.get('AWS_AUTH_REGION_NAME')

logging.basicConfig(format=u'%(levelname)-8s [%(asctime)s]  %(message)s',
                    level=logging.INFO)

if os.path.exists("/tmp/backup"):
    logging.info("Folder for backups already exist. Skip.")
else:
    os.mkdir("/tmp/backup")
    logging.info("Folder for backups created.")

# Connect to vault and getting connect url
client = hvac.Client(
    url=VAULT_ADDR,
    token=VAULT_SECRET
)

print()

try:
    client.renew_token(increment=60 * 60 * 72)
except hvac.exceptions.InvalidRequest as _:
    # Swallow, as this is probably a root token
    pass
except hvac.exceptions.Forbidden as _:
    # Swallow, as this is probably a root token
    pass
except Exception as e:
    exit(e)

conn = S3Connection(
    host=AWS_STORAGE_URL,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

conn.auth_region_name = AWS_AUTH_REGION_NAME

bucket = conn.get_bucket(AWS_BUCKET_NAME)

k = Key(bucket)

# Logging params

connect_true = client.is_authenticated()

if connect_true:
    logging.info("Connected. Client authenticated.")
else:
    logging.warning("Not connected or client not authenticated.")

secrets_engines_list = client.sys.list_mounted_secrets_engines()
secret_list = sorted(secrets_engines_list.keys())

db_connects_array = []

for kv in secret_list:
    rgxMount = re.compile(
        'cubbyhole/|identity/|auth|warnings|wrap_info|sys/|shared/|request_id|lease_id|renewable|lease_duration|data|metadata'
    )
    customer_name = rgxMount.sub('', kv)

    if len(customer_name) == 0:
        continue

    if customer_name.find('/') != -1:
        customer_name = customer_name[:-1]

    try:
        env_list = client.secrets.kv.v2.list_secrets(
            path=PATH_TO_SECRETS, mount_point=customer_name + '/')
        for env_name in env_list['data']['keys']:
            try:
                vault_secret = client.secrets.kv.v2.read_secret_version(
                    path=PATH_TO_SECRETS + env_name + '/database',
                    mount_point=customer_name + '/'
                )

                key_exists = '.skip_database_backup' in vault_secret['data']['data']

                u = vault_secret['data']['data']['connect_url']

                rgx = re.compile(
                    'jdbc:|&sslfactory=org.postgresql.ssl.NonValidatingFactory&sslmode=require|&targetServerType=master'
                )
                connect_url = rgx.sub('', u)

                if not key_exists:
                    db_connects_array.append(
                        {'customer_name': customer_name, 'env_name': env_name, 'connect_url': connect_url})
            except:
                logging.warning("Database param not found for " +
                                customer_name + " in environment " + env_name)
    except:
        logging.warning("Path not found " + customer_name)
    try:
        env_list2 = client.secrets.kv.v2.list_secrets(
            path=PATH_TO_SECRETS2, mount_point=customer_name + '/')
        for env_name in env_list2['data']['keys']:
            try:
                vault_secret2 = client.secrets.kv.v2.read_secret_version(
                    path=PATH_TO_SECRETS2 + env_name + '/database',
                    mount_point=customer_name + '/'
                )

                key_exists = '.skip_database_backup' in vault_secret2['data']['data']

                ur = vault_secret2['data']['data']['connect_url']

                rgx = re.compile(
                    'jdbc:|&sslfactory=org.postgresql.ssl.NonValidatingFactory&sslmode=require|&targetServerType=master'
                )
                connect_url = rgx.sub('', ur)

                if not key_exists:
                    db_connects_array.append(
                        {'customer_name': customer_name, 'env_name': env_name, 'connect_url': connect_url})
            except:
                logging.warning("Database param not found for " +
                                customer_name + " in environment " + env_name)
    except:
        logging.warning("Path not found " + customer_name)
i = len(db_connects_array)

for i in range(0, i):
    try:
        database_uri = db_connects_array[i]['connect_url']
        customer_name1 = db_connects_array[i]['customer_name']
        env_name1 = db_connects_array[i]['env_name']

        if env_name1.find('/') != -1:
            env_name1 = env_name1[:-1]

        now = date.today()
        FILENAME_PREFIX = ('backup' + "_" + customer_name1 + "_" + env_name1)
        filename = (FILENAME_PREFIX + "_" + str(now) + ".sql.gz")
        BACKUP_PATH = r'/tmp/backup'
        destination = r'%s/%s' % (BACKUP_PATH, str(filename))

        logging.info('Starting backup for ' +
                     customer_name1 + "-" + env_name1 + "/" + filename)
        ps = subprocess.Popen(
            ['pg_dump', database_uri, '--compress=9',
             '-c', '-O', '-f', destination],
            stdout=subprocess.PIPE)
        output = ps.communicate()[0]
        logging.warning('Info: Upload ' + filename + ' to ' +
                        customer_name1 + "-" + env_name1 + "/" + filename)
        k.key = (customer_name1 + "/" + env_name1 + "/" + filename)
        k.set_contents_from_filename(destination)
        os.remove(destination)
        logging.info('Backup completed for ' +
                     customer_name1 + "-" + env_name1)
    except:
        logging.warning('Exception. Backup skipped')

if os.path.exists("/tmp/backup"):
    shutil.rmtree("/tmp/backup/")
    logging.info("Folder for backups deleted.")
else:
    logging.warning("Folder for backups not found.")

logging.info('Backups completed')
