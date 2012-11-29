import psycopg2
import redis


def fillredis():
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
                        pipe.hset(ith[1], part, row[1])
                    except:
                        pass
    pipe.execute()

fillredis()
