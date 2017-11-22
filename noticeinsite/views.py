from . import app
from flask import render_template
from flask import abort
from datetime import date
import datetime
import boto3
import botocore
import collections
import jinja2
import os
import logging

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def index(path):
    if "STAGE" in os.environ:
        stage = os.environ['STAGE']
    else:
        stage = 'dev'

    s3Bucket = 'noticeinsite-' + stage + '-data.arlindo.ca'

    s3 = boto3.client('s3')

    if path is not "" and not path.endswith("/"):
        path = path + '/'
    if path is not "" and not doesS3PathKeyExist(s3,s3Bucket,path):
        logging.error('Company not found %s', path)
        abort(404)

    companydatafiles = {}

    companydatafiles = getFolderFileListAndFilterData(s3,s3Bucket,path)

    return render_template('index.html',companydatafiles=companydatafiles,path=path)

@app.errorhandler(404)
def handle_404(error):
    return render_template('404.html'), 404

@app.errorhandler(Exception)
def handle_error(e):
    return render_template('500.html'), 500

def doesS3PathKeyExist(client, bucket, key):
    keyfound = False
    result=client.list_objects_v2(Bucket=bucket, MaxKeys=1, Prefix=key)
    for obj in result.get('Contents', []):
        if key in obj['Key']:
            keyfound = True
            break

    return keyfound

def getMetaData(client,bucket,keypath):

    result = client.get_object(Bucket=bucket, Key=keypath)
    text = result['Body'].read()

    metakeyvalues = {}

    lines = text.splitlines()
    for line in lines:
        var, val = line.split("=")
        var = var.strip()
        val = val.strip()
        if val.startswith('"') and val.endswith('"'):
            val = val[1:-1]
        metakeyvalues[var] = val
    return metakeyvalues

def validMetakeyfile(metakeyvalues):
    try:
        value = metakeyvalues['ExpDate']
        value = metakeyvalues['StartDate']
        value = metakeyvalues['EventType']
        value = metakeyvalues['PhoneNum']
        value = metakeyvalues['EventDate']
        value = metakeyvalues['ClientName']
        return True
    except KeyError:
        logging.error('Invalid metadata file found')
        return False

def getFolderFileListAndFilterData(client,bucket,keypath):

    foldersfiles = {}
    if keypath.endswith("/"):
        keypath = keypath[:-1]

    for folder in folders(client,bucket,keypath):
        logging.info('Company Folder Name %s', folder)
        for subfolder in folders(client,bucket,prefix=folder):
            logging.info('Company SubFolder Name %s', subfolder)
            if doesS3PathKeyExist(client,bucket,subfolder + 'meta.txt'):
                metakeyvalues = getMetaData(client,bucket,subfolder + 'meta.txt')

                if validMetakeyfile(metakeyvalues):
                    expiredate = datetime.datetime.strptime(metakeyvalues['ExpDate'], "%b,%d,%Y")
                    startdate = datetime.datetime.strptime(metakeyvalues['StartDate'], "%b,%d,%Y")

                    today = datetime.datetime.now().strftime("%b,%d,%Y")
                    today = datetime.datetime.strptime(today,"%b,%d,%Y")
                    if today < expiredate and today >= startdate:

                        foldersfiles.setdefault(subfolder,{})
                        foldersfiles[subfolder]['companyinfo'] = metakeyvalues
                        foldersfiles[subfolder].setdefault('files',[])

                        for file in files(client,bucket,prefix=subfolder):
                            if not file.endswith("/"):
                                if "meta.txt" not in file:
                                    #furl = '{}/{}/{}'.format(client.meta.endpoint_url, bucket, file)
                                    furl = client.generate_presigned_url('get_object', Params = {'Bucket': bucket, 'Key': file}, ExpiresIn = 86400)
                                    foldersfiles[subfolder]['files'].append(furl)
    return collections.OrderedDict(sorted(foldersfiles.items()))

def folders(client, bucket, prefix=''):
    paginator = client.get_paginator('list_objects_v2')
    for result in paginator.paginate(Bucket=bucket, Prefix=prefix, Delimiter='/'):
        for prefix in result.get('CommonPrefixes', []):
            yield prefix.get('Prefix')

def files(client, bucket, prefix=''):
    paginator = client.get_paginator('list_objects_v2')
    for result in paginator.paginate(Bucket=bucket, Prefix=prefix, Delimiter='/'):
        for prefix in result.get('Contents', []):
            yield prefix.get('Key')

@app.template_filter('basename')
def basename(path):
    bname = os.path.basename(path)
    if "?" in bname:
        bname = bname.partition("?")[0]
    return bname

@app.template_filter("dirname")
def dirname(path):
    if path.endswith("/"):
        path = path[:-1]
    dirname, filename = os.path.split(path)
    return dirname
