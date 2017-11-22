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
        abort(404)

    companydatafiles = {}

    companydatafiles = getFolderFileListAndFilterData(s3,s3Bucket,path)

    return render_template('index.html',companydatafiles=companydatafiles)

@app.errorhandler(404)
def handle_404(error):
    return render_template('404.html'), 404

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

def getFolderFileListAndFilterData(client,bucket,keypath):

    foldersfiles = {}
    if keypath.endswith("/"):
        keypath = keypath[:-1]

    print 'keypath:' + keypath
    rs=client.list_objects_v2(Bucket=bucket, Delimiter='/', Prefix=keypath)
    if rs.get('CommonPrefixes') is not None:
        for subdir in rs.get('CommonPrefixes'):
            print "Dir:" + subdir.get('Prefix')
            subdirkey = subdir.get('Prefix')

            if doesS3PathKeyExist(client,bucket,subdirkey + 'meta.txt'):
                metakeyvalues = getMetaData(client,bucket,subdirkey + 'meta.txt')

                expiredate = datetime.datetime.strptime(metakeyvalues['ExpDate'], "%b,%d,%Y")
                startdate = datetime.datetime.strptime(metakeyvalues['StartDate'], "%b,%d,%Y")

                today = datetime.datetime.now().strftime("%b,%d,%Y")
                today = datetime.datetime.strptime(today,"%b,%d,%Y")
                if today < expiredate and today >= startdate:
                    rs = client.list_objects_v2(Bucket=bucket,
                                    Prefix=subdirkey,
                                    Delimiter='/'
                                    )
                    if subdirkey.endswith("/"):
                        subdirkey = subdirkey[:-1]

                    foldersfiles.setdefault(subdirkey,{})

                    foldersfiles[subdirkey]['companyinfo'] = metakeyvalues

                    print foldersfiles

                    foldersfiles[subdirkey].setdefault('files',[])

                    if rs.get('Contents') is not None:
                        for file in rs.get('Contents'):
                            print "file:" + file.get('Key')
                            filekey = file.get('Key')

                            if not filekey.endswith("/"):
                                if "meta.txt" not in filekey:
                                    furl = '{}/{}/{}'.format(client.meta.endpoint_url, bucket, filekey)
                                    foldersfiles[subdirkey]['files'].append(furl)

    print foldersfiles
    return collections.OrderedDict(sorted(foldersfiles.items()))


@app.template_filter('basename')
def basename(path):
    return os.path.basename(path)
