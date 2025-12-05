#!/bin/sh

# # Get new schema name as string from first argument
# if [ "$#" != 3 ]; then
#     echo "Must pass 2 arguments to this file.\n1) Database, 2) Schema Name and \n3)Postgis Required? [0 or 1]"
#     exit 0
# else
DATABASE=$1
SCHEMA_NAME=$2
# POSTGIS_REQUIRED=$3
# fi

docker exec postgres_container \
        sh -c "psql -d ${DATABASE} -U sheldon -v new_schema_name=${SCHEMA_NAME} -a -q -f ./home/create_schema.sql"

# if [ ${POSTGIS_REQUIRED} == 1 ]; then
#     docker exec postgres_container \
#         sh -c "psql -d ${DATABASE} -U sheldon -v new_schema_name=${SCHEMA_NAME} -a -q -f ./home/setup_extension_postgis.sql"
#     echo "New Schema Name is: $SCHEMA_NAME with postgis extension"
# else
echo "New Schema Name is: $SCHEMA_NAME"
# fi
