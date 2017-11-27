import os
import json


class dirs:
    script_dir = os.path.dirname(os.path.realpath(__file__))
    root_dir = os.path.dirname(os.path.realpath('{}../'.format(script_dir)))


def prechecks():
    executables = ['docker-machine', 'rsync']
    env = ['DIGITALOCEAN_ACCESS_TOKEN']
    for e in executables:
        if os.system('command -v {} >/dev/null'.format(e)) != 0:
            print('{} must be installed to run this script'.format(e))
            exit(1)
    for v in env:
        if not os.getenv(v, False):
            print('Cannot locate environment variable {}'.format(v))
            exit(1)


def server_meta():
    with open('{}/package.json'.format(os.getcwd())) as packagejson:
        file = json.load(packagejson)
        return file['server']
