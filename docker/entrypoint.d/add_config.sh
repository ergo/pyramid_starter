#!/bin/bash

#copy fresh config if missing
if [ ! -f /opt/rundir/config.ini ]; then
  set +e
  gosu application ln -s /opt/application/$APP_INI_FILE /opt/rundir/config.ini
  set -e
fi

if [ "$APP_ENV" = 'development' ]; then

  if [ ! -f /opt/rundir/testing.ini ]; then
    set +e
    gosu application cp /opt/application/$APP_INI_FILE /opt/rundir/$TESTING_INI
    sed -i "s/@db:5432\/test/@db:5432\/test_runner/" /opt/rundir/$TESTING_INI
    set -e
  fi

fi


