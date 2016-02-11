#!/usr/bin/env python
import base64
import glob
import os
import zipfile
from StringIO import StringIO

import click
import boto3


@click.command()
def deploy():
    func_name = 'hs_bot_webhook'
    boto3.set_stream_logger()

    buf = StringIO()
    with zipfile.ZipFile(buf, 'w') as z:
        for f in glob.glob(os.path.join(os.path.dirname(__file__), 'app/*.py')):
            z.write(os.path.abspath(f), os.path.basename(f))
    buf.seek(0)
    pkg = base64.b64encode(buf.read())

    client = boto3.client('lambda')
    res = client.update_function_code(
        FunctionName=func_name,
        ZipFile=pkg,
        Publish=False
    )
    assert res['FunctionName'] == func_name
    # code_sha256 = res['CodeSha256']
    version = res['version']
    click.echo('Function {n} sources updated. Version {v}'.format(
        n=func_name, v=version))


if __name__ == '__main__':
    deploy()
