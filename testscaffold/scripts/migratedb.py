from __future__ import print_function

import os
import sys

from alembic import command
from alembic.config import Config
from pyramid.paster import (
    get_appsettings,
    setup_logging,
)
from pyramid.scripts.common import parse_vars


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri> [var=value]\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)


def main(argv=sys.argv):
    if len(argv) < 2:
        usage(argv)
    config_uri = argv[1]
    options = parse_vars(argv[2:])
    setup_logging(config_uri)
    settings = get_appsettings(config_uri, name='testscaffold',
                               options=options)
    alembic_cfg = Config()
    alembic_cfg.set_main_option(
        'script_location', 'ziggurat_foundations:migrations')
    alembic_cfg.set_main_option('sqlalchemy.url', settings['sqlalchemy.url'])
    command.upgrade(alembic_cfg, 'head')
    alembic_cfg = Config()
    alembic_cfg.set_main_option(
        'script_location', 'testscaffold:migrations')
    alembic_cfg.set_main_option('sqlalchemy.url', settings['sqlalchemy.url'])
    command.upgrade(alembic_cfg, 'head')
