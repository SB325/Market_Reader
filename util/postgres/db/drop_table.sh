#!/bin/sh

# Get new schema name as string from first argument
if [ "$#" != 3 ]; then
    echo "Must pass 2 arguments to this file: 1) Database, 2) Schema and 3) Name of table to drop."
    exit 0
else
    DATABASE=$1
    SCHEMA=$2
    TABLE_TO_DROP=$3
fi
docker exec postgres_container \
        sh -c "psql -d ${DATABASE} -U sheldon -v schema=${SCHEMA} -v table_to_drop=${TABLE_TO_DROP}  -a -q -f /home/drop_bantam_table.sql"