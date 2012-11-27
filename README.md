osmhelpertools
==============

Tools to fix OSM Data.

The following tools are provided to help with OSM
 * geocoder : Geocoder for Colombia
 * botika : bot to fix things related to Colombia
 * colombiahelper : tools that help people to fix data



Work in progress
================

Cleaning intersections.

Find the intersections::

	SELECT w.id AS wayid, w.tags -> 'name' AS name, n.id as pid, x(n.geom) as lon, y(n.geom) as lat from ways w, nodes n where w.tags -> 'highway' = 'residential' AND w.tags ? 'name' AND n.id = any(w.nodes) ORDER BY w.id, w.tags -> 'name', n.id;

Find the points that have more than two names::
	
	SELECT count(name), id FROM (SELECT distinct w.tAgs -> 'name' AS name, n.id FROM ways w, nodes n WHERE w.tags -> 'highway' = 'residential' AND w.tags ? 'name' AND n.id = any(w.nodes)) AS sub GROUP BY id HAVING count(name) > 2;

SELECT n2.geom, n2.id FROM (SELECT count(name), id FROM (SELECT distinct w.tAgs -> 'name' AS name, n.id FROM ways w, nodes n WHERE w.tags -> 'highway' = 'residential' AND w.tags ? 'name' AND n.id = any(w.nodes)) AS sub GROUP BY id HAVING count(name) > 2) AS s1, nodes n2 WHERE s1.id = n2.id;

Use clustering to show on zoom out, use detail when zooming in somewhere.
