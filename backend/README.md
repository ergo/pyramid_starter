# testscaffold README

# # install precommit

    curl https://pre-commit.com/install-local.py | python -
    pre-commit install

The application should be visible under http://127.0.0.1:6543

## docker dev start
    USER_UID=`id -u` USER_GID=`id -g` docker-compose up -d

## running test suite

    USER_UID=`id -u` USER_GID=`id -g` TEST_INI="config.ini" docker-compose run --rm app pytest ../application

## update packages

    USER_UID=`id -u` USER_GID=`id -g` docker-compose run --rm app bash
    cd ../application; /opt/venv/bin/pip-compile requirements.in

    # bump package to specific version
    cd ../application; /opt/venv/bin/pip-compile --upgrade-package requests==2.20.0

    # compile dev requirements
    cd ../application; /opt/venv/bin/pip-compile requirements-dev.in


Finally fix permissions on generated files (sometimes they get generated as root user):

    chmod 664 requirements.txt requirements-dev.txt

## to rebuild the image after packages updated

    docker-compose build app

## to add alembic migration files

    USER_UID=`id -u` USER_GID=`id -g` docker-compose run --rm app bash
    cd ../application; alembic -c ../rundir/config.ini revision -m "migration name"

## to run db alembic

    USER_UID=`id -u` USER_GID=`id -g` docker-compose run --rm app bash
    migrate_testscaffold_db config.ini

## to populate database with entries

    USER_UID=`id -u` USER_GID=`id -g` docker-compose run --rm app bash
    initialize_testscaffold_db config.ini

## to access postgresql

    USER_UID=`id -u` USER_GID=`id -g` docker-compose run --rm db psql -h db -U test #password: test

To access pgadmin go to http://127.0.0.1:5434

Credentials: `test@test@webreactor.eu`

When creating new db connection use:

dbhost: db
user: test
password: test


# Working with Translations

First open up shell

    USER_UID=`id -u` USER_GID=`id -g` docker-compose run --rm app bash
    cd ../application;

Create pot file

    pot-create -c message-extraction.ini \
    -o testscaffold/locale/testscaffold.pot \
    --package-name testscaffold testscaffold

create new PO files for specific language:

    mkdir -p testscaffold/locale/nl/LC_MESSAGES
    msginit -l nl -i testscaffold/locale/testscaffold.pot -o testscaffold/locale/nl/LC_MESSAGES/testscaffold.po

update PO files for specific language:

    msgmerge --update testscaffold/locale/en/LC_MESSAGES/testscaffold.po testscaffold/locale/testscaffold.pot

compile translations

    msgfmt -o testscaffold/locale/en/LC_MESSAGES/testscaffold.mo \
          testscaffold/locale/en/LC_MESSAGES/testscaffold.po

    msgfmt -o testscaffold/locale/pl/LC_MESSAGES/testscaffold.mo \
          testscaffold/locale/pl/LC_MESSAGES/testscaffold.po
