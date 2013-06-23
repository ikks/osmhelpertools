CREATE OR REPLACE FUNCTION reversegeo(lat float, lon float) RETURNS text AS $$
pnt = u'Point({0} {1})'.format(lon, lat)
mp = 10
q1 = u"""SELECT l.*, w.nodes 
FROM osm_line l
JOIN osm_ways w ON l.osm_id = w.id
WHERE buffer(PointFromText('{0}', 4326), .001) && l.way
AND (l.railway IS NULL AND l.name IS NOT NULL AND l.name != '')
AND intersects(way
  , buffer(PointFromText('{0}', 4326), .002)
)
ORDER BY distance(way, PointFromText('{0}', 4326)) 
LIMIT 1""".format(pnt)
rv = plpy.execute(q1)

if len(rv) == 0:
    return u''
# Found the closest way to the given point
nodes = u",".join([str(i) for i in rv[0]["nodes"]])

way_id = rv[0]["osm_id"]
way_name = rv[0]["name"]

nq = plpy.execute(u"""SELECT n.id, x(n.geom) AS lon, y(n.geom) AS lat
, distance_sphere(PointFromText('{0}', 4326), n.geom) AS dist
FROM nodes n
WHERE n.id IN ({1})
ORDER BY distance(n.geom, PointFromText('{0}', 4326))
LIMIT {2}""".format(pnt, nodes, mp))
intersecting_ways = set()
for node in nq:
    # looking at the intersecting points in the way, from the closest to the farest
    inq = plpy.execute(u"""SELECT l.name, l.osm_id
        FROM osm_line l
        JOIN way_nodes wn
        ON l.osm_id = wn.way_id
        WHERE wn.node_id = {0}
        AND wn.way_id != {1}
        AND l.name IS NOT NULL AND l.name != ''""".format(node['id'], way_id))
    for way in inq:
        # We find the names of the ways
        if way['osm_id'] != way_id and way['name'].upper() != way_name.upper():
            intersecting_ways.add(way['name'])
return "{0}#{1}".format(way_name, ','.join(sorted(list(intersecting_ways))))
$$ LANGUAGE plpythonu;
