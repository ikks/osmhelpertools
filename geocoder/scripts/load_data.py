import psycopg2
import redis


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
    r = redis.Redis(host='localhost', port=6379, db=0)
    pipe = r.pipeline()
    conn = psycopg2.connect(
        "dbname='osm' user='osm' host='localhost' password='osm'"
    )
    cursor = conn.cursor()
    cursor.execute("SELECT names,latlon FROM intersections")
    thing = {}
    for row in cursor.fetchall():
        names = row[0].split(',')
        for i in range(len(names)):
            ith = names[i].split('|')
            for j in range(len(names)):
                jth = names[j].split('|')
                if i != j:
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
                        if key not in thing:
                            thing[key] = {key2: value}
                        elif key2 not in thing[key]:
                            thing[key][key2] = value
                        elif thing[key][key2].find(value) == -1:
                            thing[key][key2] += "|" + value
                    except:
                        pass
    for keys in thing:
        for key in thing[keys]:
            pipe.hset(keys, key, thing[keys][key])
    pipe.execute()

fillredis()
