#!/bin/bash

if [ -f /opt/rundir/celerybeat.pid ]; then
  set +e
  rm /opt/rundir/celerybeat.pid
  set -e
fi
