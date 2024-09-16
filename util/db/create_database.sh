#!/bin/sh

# Get new schema name as string from first argument
if [ "$#" != 1 ]; then
    echo "Must pass 1 argument to this file.\n1) Database Name."
    exit 0
fi
DATABASE_NAME=$1

docker exec postgres_container \
        sh -c "psql -d postgres -U sheldon -v new_db_name=${DATABASE_NAME} -a -q -f ./home/create_database.sql"

echo "${DATABASE_NAME} Created."