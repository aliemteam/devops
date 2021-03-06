#!/usr/bin/env python3
"""
Performs deployment of project files.

Direction of file transfer: Local -> Production

Deletions are performed on production side. Old assets are removed before
pushing new ones to ensure the removal of stale files.
"""
from argparse import ArgumentParser
from os.path import isfile

from shared import CommandRunner, Has


def parse_args():
    """Return parsed command line arguments."""
    parser = ArgumentParser()
    parser.add_argument(
        '-a',
        '--all',
        help='Deploy all plugins, base theme, and child theme',
        action='store_true')
    parser.add_argument(
        '-i',
        '--initial',
        help='Deploy everything including configs, database, & uploads',
        action='store_true')
    return parser.parse_args()


class Deploy(object):
    """Perform all deploy actions."""

    def __init__(self) -> None:
        self.cmd = CommandRunner()
        self.meta = {
            **self.cmd.meta,
            'root': self.cmd.dirs.root,
        }

    def site(self) -> None:
        """Deploy site files."""
        print('Removing old version of {name}...'.format(**self.meta))
        self.cmd.ssh(
            'rm -rf /home/{name}/app/wp-content/themes/{name}/*'.format(
                **self.meta))

        print('Deploying docker-compose files...')
        self.cmd.rsync(
            '{root}/docker-compose.yml'.format(**self.meta),
            '{name}:/home/{name}/app/docker-compose.yml'.format(**self.meta))
        self.cmd.rsync(
            '{root}/lib/production.yml'.format(**self.meta),
            '{name}:/home/{name}/app/docker-compose.override.yml'.format(
                **self.meta))

        print('Deploying {name}...'.format(**self.meta))
        self.cmd.rsync(
            '{root}/dist/'.format(**self.meta),
            '{name}:/home/{name}/app/wp-content/themes/{name}'.format(
                **self.meta))

    def initial(self) -> None:
        """Deploy everything.

        This should only be ran once after initially building a new droplet.
        Deploys all configuration and project files as well as all uploads.
        """
        for filename in ['.env', 'lib/production.yml', 'data/database.sql']:
            if not isfile('{root}/{file}'.format(file=filename, **self.meta)):
                raise FileNotFoundError('File "{file}" could not be found'
                                        .format(file=filename))

        print('Deploying .env...')
        self.cmd.rsync('{root}/.env'.format(**self.meta),
                       '{name}:/home/{name}/app/.env'.format(**self.meta))

        print('Deploying database...')
        self.cmd.rsync(
            '{root}/data/database.sql'.format(**self.meta),
            '{name}:/home/{name}/app/data/database.sql'.format(**self.meta))

        print('Deploying uploads...')
        self.cmd.rsync(
            '{root}/wp-content/uploads'.format(**self.meta),
            '{name}:/home/{name}/app/wp-content'.format(**self.meta))

    def theme(self) -> None:
        """Deploy base theme if one exists."""
        if 'base_theme' not in self.meta:
            print('No base theme defined. Skipping...')
            return

        print('Removing old version of {base_theme}...'.format(**self.meta))
        self.cmd.ssh('rm -rf /home/{name}/app/wp-content/themes/{base_theme}/*'
                     .format(**self.meta))

        print('Deploying {base_theme}...'.format(**self.meta))
        self.cmd.rsync(
            '{root}/wp-content/themes/{base_theme}'.format(**self.meta),
            '{name}:/home/{name}/app/wp-content/themes'.format(**self.meta))

    def plugins(self) -> None:
        """Deploy all plugins."""
        for plugin in self.meta['plugins']:
            print('Removing old version of plugin "{plugin}"'
                  .format(plugin=plugin))
            self.cmd.ssh(
                'rm -rf /home/{name}/app/wp-content/plugins/{plugin}/*'.format(
                    plugin=plugin, **self.meta))

            print('Deploying plugin "{plugin}"'.format(plugin=plugin))
            self.cmd.rsync('{root}/wp-content/plugins/{plugin}'.format(
                plugin=plugin, **self.meta),
                           '{name}:/home/{name}/app/wp-content/plugins'.format(
                               **self.meta))

    def finalize(self) -> None:
        """Adjust ownership of project files on remote filesystem"""
        print('Adjusting filesystem permissions on remote host...')
        self.cmd.ssh('sudo chown -R www-data:{name} /home/{name}/app'
                     .format(**self.meta))


def main():
    """Main entrypoint."""
    args = parse_args()
    Has.executable('docker-machine', 'rsync')
    deploy = Deploy()
    if args.initial:
        deploy.initial()
        if not args.all:
            deploy.theme()
            deploy.plugins()
    if args.all:
        deploy.theme()
        deploy.plugins()
    deploy.site()
    deploy.finalize()


if __name__ == '__main__':
    main()
