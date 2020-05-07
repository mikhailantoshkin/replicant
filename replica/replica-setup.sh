#!/bin/bash
set -ex

echo "*:*:*:$PG_REP_USER:$PG_REP_PASSWORD" > ~/.pgpass

chmod 0600 ~/.pgpass

rm -rf ${PGDATA}/*
until pg_basebackup -h ${PG_MASTER_HOST} -D ${PGDATA} -U ${PG_REP_USER} -R -Xs -c fast -l 'initial clone' -P -v -w
    do
        echo "Waiting for master to connect..."
        sleep 1s
done

echo "host replication all 0.0.0.0/0 md5" >> "$PGDATA/pg_hba.conf"

chown postgres:postgres ${PGDATA} -R
chmod 700 ${PGDATA} -R

exec "$@"