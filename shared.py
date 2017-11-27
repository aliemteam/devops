import os
import json
import subprocess
from textwrap import dedent
from sys import exit


class dirs:
    script_dir = os.path.dirname(os.path.realpath(__file__))

    @staticmethod
    def root_dir():
        path = dirs.script_dir
        root_path = ''
        while not root_path:
            if os.path.isfile('{}/package.json'.format(path)):
                root_path = path
            if path == '/':
                raise FileNotFoundError(
                    'Hit OS directory root without finding a package.json file'
                )
            path = os.path.dirname(os.path.realpath('{}../'.format(path)))
        return root_path


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
    with open('{}/package.json'.format(dirs.root_dir())) as packagejson:
        file = json.load(packagejson)
        return file['server']


def ssh_init():
    meta = server_meta()
    has_docker_machine = subprocess.getoutput(
        'docker-machine ls -q --filter "name={name}" | wc -l'.format(
            name=meta['name'])) == '1'
    has_ssh = subprocess.getoutput(
        'grep -c "Host {name}" ~/.ssh/config'.format(name=meta['name'])) == '1'
    if has_docker_machine:
        return ('docker-machine', 'scp -rd')
    elif has_ssh:
        return ('rsync', '-avz')
    else:
        print(
            dedent("""
        ERROR: Could not locate a docker-machine or ssh identity for {name}

        To enable SSH connections, add the following to your ~/.ssh/config file:

        Host {name}
            HostName <ip-address-of-server>
            Port 22
            User {name}
            IdentityFile ~/.ssh/<name-of-our-private-key-file>

        """.format(name=meta['name'])))
        exit(1)
