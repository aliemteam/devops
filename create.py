#!/usr/bin/env python3
"""
Creates, provisions, and configures new remote docker-machine on DigitalOcean
running Ubuntu.
"""
from json import load
from os import getenv
from tempfile import NamedTemporaryFile
from urllib.request import urlopen

from shared import CommandRunner, Has, Provider


def docker_compose_version() -> str:
    """Fetch and return latest version of Docker Compose"""
    docker_compose = load(
        urlopen('https://api.github.com/repos/docker/compose/releases'))
    return docker_compose[0]['tag_name']


def create_machine() -> str:
    """Create docker-machine on DigitalOcean."""
    name = input('--> Droplet name: ')
    size = input('--> Droplet size [2gb]: ') or 's-1vcpu-2gb'
    dirname = CommandRunner.dirs.script
    with NamedTemporaryFile(mode='w+') as tmp:
        with open('{}/cloud-config.yml'.format(dirname)) as config:
            ssh_users = ', '.join([
                '"{}"'.format(x.strip()) for x in input(
                    '--> Additional SSH users (format: gh:githubuser): ')
                .split(',') if x
            ])
            tmp.write(config.read().format(
                name=name,
                ssh_users=ssh_users,
                docker_compose_version=docker_compose_version()))
            tmp.flush()
        command = ('docker-machine create '
                   '--driver digitalocean '
                   '--digitalocean-access-token={token} '
                   '--digitalocean-size={size} '
                   '--digitalocean-backups=true '
                   '--digitalocean-userdata={userdata_file} '
                   '--digitalocean-monitoring '
                   '{machine_name}').format(
                       token=getenv('DIGITALOCEAN_ACCESS_TOKEN'),
                       size=size,
                       userdata_file=tmp.name,
                       machine_name=name)
        CommandRunner.run(command)
    return name


def main() -> None:
    """Main entrypoint."""
    Has.env('DIGITALOCEAN_ACCESS_TOKEN') \
       .executable('docker-machine', 'rsync')

    provider = Provider(getenv('DIGITALOCEAN_ACCESS_TOKEN'))

    machine_name = create_machine()
    provider.add_dns_records(machine_name)


if __name__ == '__main__':
    main()
