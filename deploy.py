#!/usr/bin/env python
import glob
import re
import os
import tempfile
import zipfile
from StringIO import StringIO

import click
import boto3


@click.command()
def deploy():
    func_name = 'hs_bot_webhook'
    bucket_name = 'hs-bot'
    bucket = boto3.resource('s3').Bucket(bucket_name)
    s3_key = upload_sources(bucket, func_name, 'alfa')

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


def upload_sources(bucket, name, version):
    s3_key = '{n}_{v}.zip'.format(n=name, v=version)
    s3_obj = bucket.Object(s3_key)

    buf = StringIO()
    with zipfile.ZipFile(buf, 'w') as z:
        # Compile all app sources into one temporary file and write it to the
        # zip file as function.py. The profit of deploying single file is
        # enabled inline editor on AWS Lambda console, it's handy for
        # quick fixing and hacking on produciton.
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            imp = re.compile(r'^import\s+\S+?$')
            frm = re.compile(r'^from\s+(\S+)\s+import\s+(.+)$')
            con = re.compile(r'^[A-Z_]+\s+=')

            head_import = set()
            head_from = set()
            head_future = set()
            constants = []
            code = []
            empty_count = 0

            for py in glob.glob(os.path.join(os.path.dirname(__file__), 'app/*.py')):
                name = os.path.basename(py)
                if name.startswith('_'):
                    continue

                with open(py, 'r') as src:
                    is_constants = name.startswith('const')

                    for line in src.readlines():
                        if is_constants:
                            if line and con.match(line):
                                constants.append(line)
                            continue

                        if line.strip() == '':
                            if empty_count > 2:
                                empty_count = 0
                                continue
                            empty_count += 1
                        else:
                            empty_count = 0

                        # import ...
                        m = imp.match(line)
                        if m:
                            head_import.add(m.group(0).strip())
                            continue

                        # from ... import ...
                        m = frm.match(line)
                        if m:
                            module = m.group(1)
                            if module.startswith('.'):
                                continue
                            if module == '__future__':
                                head_future.update(re.split('\s*,\s*', m.group(2).strip()))
                            else:
                                head_from.add(m.group(0).strip())
                            continue

                        code.append(line)

            temp.write('from __future__ import ' + ', '.join(head_future) + '\n\n')
            temp.write('\n'.join(sorted(head_import)) + '\n\n')
            temp.write('\n'.join(sorted(head_from)) + '\n\n\n')
            temp.write(''.join(code).strip() + '\n\n\n')
            temp.write(''.join(constants))

        z.write(temp.name, 'function.py')

    buf.seek(0)
    s3_obj.put(Body=buf, ContentType='application/zip')

    return s3_obj.key


if __name__ == '__main__':
    deploy()
