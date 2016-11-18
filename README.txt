testscaffold README
==================

Getting Started
---------------

    cd <directory containing this file>
    $VENV/bin/pip install requirements.txt
    $VENV/bin/pip install requirements-dev.txt
    $VENV/bin/initialize_testscaffold_db development.ini
    $VENV/bin/pserve development.ini

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