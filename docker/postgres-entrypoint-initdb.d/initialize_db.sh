#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE USER test WITH PASSWORD 'test';
    CREATE DATABASE test;
    GRANT ALL PRIVILEGES ON DATABASE test TO test;
    CREATE DATABASE test_runner;
    GRANT ALL PRIVILEGES ON DATABASE test_runner TO test;
EOSQL
