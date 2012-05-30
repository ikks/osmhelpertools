#Author : Igor Támara
#Given to the public domain
#You can use this software at your own risk
#I only ask you to not use it to attack OSM.
#You have been warned that you have no warranty
#over this.  So please do not complain if
#something does not work as expected.

import OsmApi
from psycopg2 import connect
import logging
import sys

DEBUG = True
CHANGESETAUTO = True
DBHOST = "localhost"
DBNAME = "osm"
LOGFILE = "/tmp/botika.log"
FORMAT = '%(asctime)-15s %(levelname)s:%(message)s'
MAXCLUSTER = 50

try:
    from conf import *
except:
    print """You must set APPID, USER, PASSWORD, API, CHANGESETAUTOTAGS, DBPASS, DBUSER, all are unicode strings, except this one : CHANGESETAUTOTAGS = {u"comment":u"Fixing Street Names"}"""
    sys.exit(0)
print PASSWORD

sys.exit(0)

replacements = {
    "CRA|CR|KR|KRA" : "Carrera",
    "CL|CLL" : "Calle",
    "DG|DIAG" : "Diagonal",
    "TR|TRANS|TV" : "Transversal",
    }

f = lambda A, n,key: dict([(key+"."+unicode(i/n), A[i:i+n]) for i in range(0, len(A), n)])

def selectstreets(cursor,client,regchange,replacement):
    """
    """
    mydict = {}
    mydictp = {}
    newdict = {}
    olddict = {}
    q = "SELECT count(*) as cant FROM ways WHERE tags ?& Array['highway','name'] AND tags -> 'name' ~* '^({0}) .*'".format(regchange)
    cursor.execute(q)
    try :
        clusters = cursor.fetchone()[0]
        clusters = clusters / MAXCLUSTER
    except :
        #No data to process!!!
        clusters = -1
    if clusters != -1:
        if clusters == 0:
            #If we have too few fixes, no need for partition
            q = "SELECT 1, l.p, l.name, l.id FROM (SELECT id,tags -> 'name' AS name, ST_AsText(ST_PointN(linestring,1)) AS  p FROM ways WHERE tags ?& Array['highway','name'] AND tags -> 'name' ~* '^({1}) .*') AS l ORDER BY name;".format(clusters,regchange)
        else :
            #If there are a lot of fixes to be done, we make a partition
            q = "SELECT kmeans(ARRAY[ST_X(l.p), ST_Y(l.p)], {0}) OVER (), l.p, l.name, l.id FROM (SELECT id,tags -> 'name' AS name, ST_AsText(ST_PointN(linestring,1)) AS  p FROM ways WHERE tags ?& Array['highway','name'] AND tags -> 'name' ~* '^({1}) .*') AS l ORDER BY kmeans,name;".format(clusters,regchange)
        cursor.execute(q)
        rows =  cursor.fetchall()
        cont = 0
        for row in rows :
            if not unicode(row[0]) in mydictp:
                mydictp[unicode(row[0])] = []
            mydictp[unicode(row[0])].append(unicode(row[3]))
        #We used kmeans to group
        #Now we make smaller groups
        for k,v in mydictp.iteritems():
            if len(v)>MAXCLUSTER:
                mydict.update(f(v,MAXCLUSTER,k))
            else :
                mydict[k]=v
        #Fetching
        for k,v in mydict.iteritems():
            logging.info("Fetching {0} ways".format(len(v)))
            olddict.update(client.WaysGet(v))        
        #Updating
        for y in olddict.itervalues():
            updw = { u'id': unicode(y[u'id']), u'nd': y[u'nd'], u'tag': y[u'tag'].copy(), u'version': y[u'version']}
            updw['tag'].update({ u'mechanical' : u'yes' })
            updw[u'tag'][u'name'] = replacement+updw[u'tag'][u'name'][updw[u'tag'][u'name'].index(" "):]
            if updw[u'tag'][u'name'] == y[u'tag'][u'name']:
                logging.warning("{0} already fixed :)".format(row[3]))
            else:
                newdict[updw[u'id']] = updw
            cont += 1
            if cont % 50 == 0: logging.info("Updated 50")
    return mydict,newdict

conn = connect("dbname='{0}' user='{1}' host='{2}' password='{3}'".format(DBNAME, DBUSER, DBHOST, DBPASS))

client = OsmApi.OsmApi(api = API, username = USER, password = PASSWORD , appid = APPID)

logging.basicConfig(filename=LOGFILE,format=FORMAT,level=logging.DEBUG)

def applychanges(conn,client,replacements) :
    logging.info("Starting batch")
    for k,v in replacements.iteritems() :
        logging.info("Replacing {0} by {1}".format(k,v))
        mydict,newdict = selectstreets(conn.cursor(),client,k,v)
        for group in mydict.values():
            l = client.ChangesetCreate(CHANGESETAUTOTAGS)
            logging.info("Processing changeset {0}".format(l))
            cont = 0
            for idw in group :
                if idw in newdict.keys() :
                    cont += 1
                    updw = newdict[idw]
                    updw[u'changeset'] = unicode(l)
                    neww = client.WayUpdate(updw)
                if cont % 50 == 0: logging.info("Saved 50")
            client.ChangesetClose()
            logging.info("Saved changeset {0}".format(l))

applychanges(conn,client,replacements)
