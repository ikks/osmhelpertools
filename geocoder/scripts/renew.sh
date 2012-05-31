#!/bin/bash
PWD=`pwd`"/localinfo.sh"
if [ -f $PWD ]
then
. $PWD
else
echo "YOU MUST configure localinfo.sh, grab a sample from localinfo.sh.sample"
exit 0;
fi;

wget "http://download.geofabrik.de/osm/south-america/"$COUNTRY".osm.bz2"
time bunzip2 $COUNTRY".osm.bz2"
dropdb $DBNAME
createdb -O $DBUSER -T template_postgis $DBNAME
time osm2pgsql -d $DBNAME -l -s -p $DBUSER $COUNTRY".osm"
psql -c "CREATE EXTENSION hstore;" $DBNAME
psql -f $OSMOSISPATHSCRIPTS"pgsnapshot_schema_0.6.sql" $DBNAME
psql -f $OSMOSISPATHSCRIPTS"pgsnapshot_schema_0.6"_linestring.sql $DBNAME
psql -f $OSMOSISPATHSCRIPTS"pgsnapshot_schema_0.6_bbox.sql" $DBNAME
psql -f $OSMOSISPATHSCRIPTS"pgsnapshot_schema_0.6_action.sql" $DBNAME
time $OSMOSIS --read-xml $COUNTRY".osm" --write-pgsql database=$DBNAME user=$DBSUPR host=$DBHOST password=$DBPSUP
psql -c "GRANT SELECT on nodes, ways, osm_line, osm_nodes, osm_ways, way_nodes to $DBUSER;" $DBNAME
psql -c "DROP DATABASE "$OLDDB";" template1 && psql -c "ALTER DATABASE "$DBNAME" RENAME TO "$OLDDB";" template1
rm "$COUNTRY".osm
