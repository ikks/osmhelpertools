# -*- coding: utf-8 -*-
from multiprocessing import Pool
from multiprocessing import cpu_count

import psycopg2
import redis


query_city = """SELECT name, ST_distance(geom,
    ST_GeomFromText('POINT({0} {1})',4326)) FROM
    places WHERE ST_distance(geom, ST_GeomFromText(
    'POINT({0} {1})',4326)) < 0.1 ORDER BY 2 LIMIT 1
"""

corrections = [
    ['Bogotá', 4.82285, -74.07052],
    ['Bogotá', 4.76050, -74.10459],
    ['Bogotá', 4.74262, -74.12803],
    ['Bogotá', 4.69463, -74.16433],
    ['Bogotá', 4.63646, -74.20527],
    ['Bogotá', 4.61379, -74.19008],
    ['Bogotá', 4.59890, -74.16116],
    ['Bogotá', 4.55544, -74.14656],
    ['Bogotá', 4.50992, -74.10820],
    ['Bogotá', 4.56733, -74.08039],
    ['Bogotá', 4.61824, -74.06211],
    ['Bogotá', 4.67607, -74.03807],
    ['Bogotá', 4.69557, -74.02572],
    ['Bogotá', 4.73595, -74.01713],
    ['Bogotá', 4.80061, -74.03155],
]


def find_city(main_key, memres, disters):
    """Finds the closest city for a dictionary of points
    main_key is the first part of the address
    memres is a dictionary that holds the second part of the address
    as the key and the value is a string of lat,lon[|lat,lon]
    disters is a list of the form city,lat,lon.

    Returns an array of the form [main_key, lat,lon,city[|lat,lon,city]]
    """
    result = {}
    for key in memres:
        to_save = []
        for elem in memres[key].split("|"):
            lat, lon = elem.split(",")
            to_save.append('{0},{1}'.format(elem, min(
                disters,
                key=lambda p: abs(p[1] - float(lat)) + abs(p[2] - float(lon)),
            )[0]))
        result[key] = "|".join(to_save)
    return [main_key, result]


def fillredis():
    """Fills a redis instance with hash of the form:
    'CARRERA 20' '40' 'lat,lon[|lat,lon]*'
    From the table intersections of the form name[|name] and lat,lon
    """
    thedict = {
        'Calle ': 1,
        'Carrera ': 1,
        'Diagonal': 1,
        'Transversal': 1,
    }

    # Holds in memory the intersections
    memres = {}
    close_factor = 0.0008

    conn = psycopg2.connect(
        "dbname='osm' user='osm' host='localhost' password='osm'"
    )
    cursor = conn.cursor()
    cursor.execute("SELECT name, lat, lon from places")
    disters = cursor.fetchall()
    disters.extend(corrections)
    cursor.execute("SELECT names,latlon FROM intersections")
    rows = cursor.fetchall()
    for row in rows:
        names = row[0].split(',')
        for i in range(len(names)):
            ith = names[i].split('|')
            for j in range(len(names)):
                jth = names[j].split('|')
                if i != j:
                    if len(ith) > 1 and len(jth) > 1 and ith[1] == jth[1]:
                        # Excluded Streets with the same name but joined
                        # with different type, for example, tertiary that
                        # becomes residential
                        continue
                    try:
                        part = jth[1]
                        try:
                            sstr = jth[1].split()[0].capitalize() + ' '
                            if thedict.get(sstr):
                                part = jth[1][jth[1].find(' ') + 1:]
                        except:
                            pass
                        key = ith[1].upper()
                        key2 = part.upper()
                        value = row[1].upper()
                        if key not in memres:
                            memres[key] = {key2: value}
                        elif key2 not in memres[key]:
                            lat, lon = value.split(',')
                            memres[key][key2] = value
                        elif memres[key][key2].find(value) == -1:
                            close = False
                            for previous in memres[key][key2].split('|'):
                                spl = previous.split(',')
                                spl2 = value.split(',')
                                dist = abs(float(spl[0]) - float(spl2[0])) + abs(
                                    float(spl[1]) - float(spl2[1])
                                )
                                if dist < close_factor:
                                    close = True
                                    break
                            if not close:
                                lat, lon = value.split(',')
                                memres[key][key2] += u"|" + value
                    except:
                        pass

    # memres holds all the intersections for redis

    # The following gets the city for the found points
    pool = Pool(processes=cpu_count() * 2)
    result = []
    for main_key in memres:
        result.append(pool.apply(find_city, (main_key, memres[main_key].copy(), list(disters))))

    # Once we have calculated all the cities
    # we replace our old redis instance with the fresh values
    r = redis.Redis(host='localhost', port=6379, db=0)
    r.flushdb()
    pipe = r.pipeline()
    for elem in result:
        for key in elem[1]:
            pipe.hset(elem[0], key, elem[1][key])
    pipe.execute()


fillredis()
