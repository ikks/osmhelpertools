#!/bin/bash
PWD=`pwd`"/localinfo.sh"
if [ -f $PWD ]
then
. $PWD
else
echo "YOU MUST configure localinfo.sh, grab a sample from localinfo.sh.sample"
exit 0;
fi;

wget "http://download.geofabrik.de/openstreetmap/south-america/"$COUNTRY".osm.bz2"
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
psql -f /usr/share/postgresql/9.1/extension/kmeans.sql $DBNAME
psql -c "SELECT *, tags -> 'name' AS name, upper(substr(tags -> 'name',0,(strpos(tags -> 'name',' ')))) AS initial,st_centroid(linestring) as centroid INTO ways_to_fix  FROM ways WHERE tags ?& Array['highway','name'] AND upper(substr(tags -> 'name',0,(strpos(tags -> 'name',' ')+1))) NOT IN ('CALLE ', 'CARRERA ', 'AVENIDA ', 'TRANSVERSAL ', 'DIAGONAL ', 'AUTOPISTA ', 'SALIDA ', 'VÍA ', 'TRONCAL ');CREATE INDEX ON ways_to_fix(id);CREATE INDEX ON ways_to_fix(name);CREATE INDEX ON ways_to_fix(initial);" $DBNAME
psql -c "SELECT n2.id, s1.count, n2.geom, s1.names INTO inter_to_fix FROM (SELECT count(name), id, string_agg(name,',') AS names FROM (SELECT DISTINCT w.tags -> 'name' AS name, n.id FROM ways w, nodes n WHERE w.tags -> 'highway' = 'residential' AND w.tags ? 'name' AND n.id = any(w.nodes)) AS sub GROUP BY id HAVING count(name) > 2) AS s1, nodes n2 WHERE s1.id = n2.id;" $DBNAME
psql -c "SELECT n2.id AS id, s1.count AS cant, y(n2.geom)||','||x(n2.geom) AS latlon, s1.names AS names INTO intersections FROM (SELECT count(name), id, string_agg(name,',') AS names FROM (SELECT DISTINCT (w.tags -> 'highway') ||'|'|| (w.tags -> 'name') AS name, n.id FROM ways w, nodes n WHERE char_length(w.tags -> 'highway') > 0  AND w.tags ? 'name' AND n.id = any(w.nodes)) AS sub GROUP BY id HAVING count(name) > 1) AS s1, nodes n2 WHERE s1.id = n2.id;" $DBNAME
psql -c "SELECT id, tags -> 'place' AS place, tags -> 'name' AS name, st_y(geom) AS lat, st_x(geom) AS lon, geom INTO lugares FROM nodes WHERE tags -> 'place' IN ('city', 'town', 'village') AND upper(tags -> 'name') NOT SIMILAR TO '(VEREDA|VDA|RESGUARDO|[0-9]%)%' ORDER BY tags -> 'name';"
psql -c "GRANT SELECT ON ways_to_fix, inter_to_fix, intersections, places TO $DBUSER;" $DBNAME
psql -c "DROP DATABASE "$OLDDB";" template1 && psql -c "ALTER DATABASE "$DBNAME" RENAME TO "$OLDDB";" template1
rm "$COUNTRY".osm
redis-cli flushdb
python load_data.py