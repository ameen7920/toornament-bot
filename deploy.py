#!/usr/bin/env python
import glob
import os
import zipfile
from StringIO import StringIO

import click
import boto3


@click.command()
def deploy():
    func_name = 'hs_bot_webhook'
    bucket_name = 'hs-bot'

    s3_key = func_name + '.zip'
    s3_obj = boto3.resource('s3').Bucket(bucket_name).Object(s3_key)

    buf = StringIO()
    with zipfile.ZipFile(buf, 'w') as z:
        for f in glob.glob(os.path.join(os.path.dirname(__file__), 'app/*.py')):
            z.write(os.path.abspath(f), os.path.basename(f))
    buf.seek(0)
    s3_obj.put(Body=buf, ContentType='application/zip')

    client = boto3.client('lambda')
    res = client.update_function_code(
        FunctionName=func_name,
        # ZipFile=pkg,
        S3Bucket=bucket_name,
        S3Key=s3_key,
        Publish=False
    )
    assert res['FunctionName'] == func_name
    # code_sha256 = res['CodeSha256']
    version = res['Version']
    click.echo('Function {n} sources updated. Version {v}'.format(
        n=func_name, v=version))


if __name__ == '__main__':
    deploy()
