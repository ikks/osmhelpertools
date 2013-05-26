import psycopg2
import sys
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

    # Holds in memory the intersections
    memres = {}
    close_factor = 0.0008

    r = redis.Redis(host='localhost', port=6379, db=0)
    pipe = r.pipeline()
    conn = psycopg2.connect(
        "dbname='osm' user='osm' host='localhost' password='osm'"
    )
    cursor = conn.cursor()
    cursor.execute("SELECT names,latlon FROM intersections")

    for row in cursor.fetchall():
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
                                memres[key][key2] += "|" + value
                    except:
                        pass

    for keys in memres:
        for key in memres[keys]:
            pipe.hset(keys, key, memres[keys][key])
    pipe.execute()

fillredis()
