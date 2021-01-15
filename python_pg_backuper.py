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
VAULT_LOGIN = os.environ.get("VAULT_LOGIN")
VAULT_PASSWORD = os.environ.get("VAULT_PASSWORD")
PATH_TO_SECRETS = os.environ.get("PATH_TO_SECRETS")
PATH_TO_SECRETS2 = os.environ.get("PATH_TO_SECRETS2")
PATH_TO_SECRETS3 = os.environ.get("PATH_TO_SECRETS3")

# Yandex S3 settings
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_BUCKET_NAME = os.environ.get("AWS_BUCKET_NAME")
AWS_STORAGE_URL = os.environ.get("AWS_STORAGE_URL")
AWS_AUTH_REGION_NAME = os.environ.get("AWS_AUTH_REGION_NAME")

logging.basicConfig(format=u'%(levelname)-8s [%(asctime)s]  %(message)s',
                    level=logging.INFO)

if os.path.exists("/tmp/backup"):
    logging.info("Folder for backups already exist. Skip.")
else:
    os.mkdir("/tmp/backup")
    logging.info("Folder for backups created.")

# Connect to vault and getting connect url
client = hvac.Client(
    url=VAULT_ADDR
)

client.auth_userpass(VAULT_LOGIN, VAULT_PASSWORD)

conn = S3Connection(
    host=AWS_STORAGE_URL,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

conn.auth_region_name = AWS_AUTH_REGION_NAME

bucket = conn.get_bucket(AWS_BUCKET_NAME)

k = Key(bucket)

connect_true = client.is_authenticated()

if connect_true == True:
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

    def loop_secrets(path_to_secret):
        try:
            env_list = client.secrets.kv.v2.list_secrets(
                path=path_to_secret, mount_point=customer_name + '/')
            for env_name in env_list['data']['keys']:
                try:
                    vault_secret = client.secrets.kv.v2.read_secret_version(
                        path=path_to_secret + env_name + '/database',
                        mount_point=customer_name + '/'
                    )

                    rg = re.compile('utrace/|/')

                    env_name1 = rg.sub('', path_to_secret)

                    key_exists = '.skip_database_backup' in vault_secret['data']['data']

                    jdbc_str = vault_secret['data']['data']['connect_url']
                    jdbc_pattern = 'postgresql://(.*?):(\d*)/(.*)\?user=(.*)\&password=(.*)\&ssl=true'

                    (j_host, j_port, j_dbname, j_username, j_password) = re.compile(
                        jdbc_pattern).findall(jdbc_str)[0]

                    clear_conn_sring = 'postgresql://' + j_host + ':' + j_port + '/' + \
                        j_dbname + '?user=' + j_username + '&password=' + j_password + '&ssl=true'

                    if not key_exists:
                        db_connects_array.append(
                            {'customer_name': customer_name, 'env_name': env_name, 'env_name1': env_name1, 'connect_url': clear_conn_sring})
                except:
                    logging.warning("Database param not found for " +
                                    customer_name + " in environment " + env_name)
        except:
            logging.warning("Path not found " + customer_name)

    loop_secrets(PATH_TO_SECRETS)

    loop_secrets(PATH_TO_SECRETS2)

    loop_secrets(PATH_TO_SECRETS3)

i = len(db_connects_array)

for i in range(0, i):
    try:
        database_uri = db_connects_array[i]['connect_url']
        customer_name = db_connects_array[i]['customer_name']
        env_name = db_connects_array[i]['env_name']
        env_name1 = db_connects_array[i]['env_name1']
        if env_name.find('/') != -1:
            env_name = env_name[:-1]

        now = date.today()
        FILENAME_PREFIX = ('backup' + "_" + customer_name + "_" + env_name)
        filename = (FILENAME_PREFIX + "_" + str(now) + ".sql.gz")
        BACKUP_PATH = r'/tmp/backup'
        destination = r'%s/%s' % (BACKUP_PATH, str(filename))

        logging.info('Starting backup for ' +
                     customer_name + "/" + env_name1 + "/" + env_name + "/" + filename)
        ps = subprocess.Popen(
            ['pg_dump', database_uri, '--compress=9',
             '-c', '-O', '-f', destination],
            stdout=subprocess.PIPE)
        output = ps.communicate()[0]
        logging.warning('Info: Upload ' + filename + ' to ' +
                        customer_name + "/" + env_name1 + "/" + env_name + "/" + filename)
        k.key = (customer_name + "/" + env_name1 +
                 "/" + env_name + "/" + filename)
        k.set_contents_from_filename(destination)
        os.remove(destination)
        logging.info('Backup completed for ' +
                     customer_name + "-" + env_name1 + "-" + env_name)
    except:
        logging.warning('Exception. Backup skipped')

if os.path.exists("/tmp/backup"):
    shutil.rmtree("/tmp/backup/")
    logging.info("Folder for backups deleted.")
else:
    logging.warning("Folder for backups not found.")

logging.info('Backups completed')
