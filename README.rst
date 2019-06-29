testscaffold README
===================

Getting Started
---------------

- ``cd <directory containing this file>``
- ``$VENV/bin/pip install -r requirements.txt``
- ``$VENV/bin/pip install -r requirements-dev.txt``
- ``$VENV/bin/pip install -e .``
- ``$VENV/bin/migrate_testscaffold_db development.ini``
- ``$VENV/bin/initialize_testscaffold_db development.ini``
- ``$VENV/bin/pserve development.ini``

Working with Translations
-------------------------

Create pot file

    pot-create -c message-extraction.ini \
    -o testscaffold/locale/testscaffold.pot \
    --package-name testscaffold testscaffold

create new PO files for specific language:

    msginit -l en -o testscaffold/locale/en/LC_MESSAGES/testscaffold.po

update PO files for specific language:

    msgmerge --update testscaffold/locale/en/LC_MESSAGES/testscaffold.po testscaffold/locale/testscaffold.pot

compile translations

    msgfmt -o testscaffold/locale/en/LC_MESSAGES/testscaffold.mo \
          testscaffold/locale/en/LC_MESSAGES/testscaffold.po

    msgfmt -o testscaffold/locale/pl/LC_MESSAGES/testscaffold.mo \
          testscaffold/locale/pl/LC_MESSAGES/testscaffold.po
