#!/bin/python
# -*- coding: utf-8 -*-
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


conn = connect("dbname='{0}' user='{1}' host='{2}' password='{3}'".format(DBNAME, DBUSER, DBHOST, DBPASS))

client = OsmApi.OsmApi(api = API, username = USER, password = PASSWORD , appid = APPID)


#This function receives an array a
#number of pieces to generate and a postfix
#to specify the names of the keys.
f = lambda A, n,key: dict([(key+"."+unicode(i/n), A[i:i+n]) for i in range(0, len(A), n)])

def selectstreets(cursor,client,regchange,replacement,countquery,onequery,kmeansquery,operation):
    """
    returns two dictionaries, the clusterisation and the complete data
    cursor : for the database
    client : OsmApi connection for reading
    regchange : expression to change
    replacement : instead of the old one
    countquery : query to count the number of elements to be operated
    onequery : query when there is no need for clustering
    kmeansquery : query when there are too much data and needs to be clustered
    operation : function that gets the old record, the new one and a replacement, returns None if the change does not apply and the new record when does
    """
    mydict = {}
    mydictp = {}
    newdict = {}
    olddict = {}
    q = countquery.format(regchange)
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
            q = onequery.format(clusters,regchange)
        else :
            #If there are a lot of fixes to be done, we make a partition
            q = kmeansquery.format(clusters,regchange)
        cursor.execute(q)
        rows =  cursor.fetchall()
        cont = 0
        for row in rows :
            if not unicode(row[0]) in mydictp:
                mydictp[unicode(row[0])] = []
            mydictp[unicode(row[0])].append(unicode(row[1]))
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
            updw = operation(y,updw,replacement)
            if updw is not None : newdict[updw[u'id']] = updw
            cont += 1
            #if cont % 50 == 0: logging.info("Updated 50")
    return mydict,newdict

logging.basicConfig(filename=LOGFILE,format=FORMAT,level=logging.DEBUG)

def applychanges(conn,client,replacements,countquery,onequery,kmeansquery,operation,basecomment) :
    """sends changes to OSM on ways
    conn : postgis with hstore database connection
    client : OSM client with write permission
    replacements : dictionary of expressions to replace
    countquery : query to count the number of elements to be operated
    onequery : query when there is no need for clustering
    kmeansquery : query when there are too much data and needs to be clustered
    operation : function that gets the old record, the new one and a replacement, returns None if the change does not apply and the new record when does    
    """
    cant = 0
    #logging.info("Starting batch")
    for k,v in replacements.iteritems() :
        logging.info(u"Replacing {0} by {1}".format(k,v))
        mydict,newdict = selectstreets(conn.cursor(),client,k,v,countquery,onequery,kmeansquery,operation)
        logging.info(u"To process {0}".format(len(newdict)))
        for group in mydict.values():
            if len(group) :
                CHANGESETAUTOTAGS[u'comment'] = basecomment+u"({0})".format(v)
                l = client.ChangesetCreate(CHANGESETAUTOTAGS)
                logging.info(u"Processing changeset {0} : {1} -> {2} ".format(l,k,v))
                cont = 0
                for idw in group :
                    if idw in newdict :
                        cont += 1
                        updw = newdict[idw]
                        updw[u'changeset'] = unicode(l)
                        neww = client.WayUpdate(updw)
                        cant += 1
                    #if cont % 50 == 0: logging.info("Saved 50")
                client.ChangesetClose()
                logging.info(u"Saved changeset {0}".format(l))
    logging.info(u"Total Ways Processed :-> {0}".format(cant))

def fixstreetname(oldw,updw,replacement):
    """Replaces the name of a street, only the first part
    """
    updw[u'tag'][u'name'] = replacement+updw[u'tag'][u'name'][updw[u'tag'][u'name'].index(" "):]
    if updw[u'tag'][u'name'] == oldw[u'tag'][u'name']:
        logging.warning("{0} already fixed :)".format(oldw[u'id']))
        return None
    return updw

def fixwaynames():
    replacements = {
    u"CARRERA|CAR|CRA|CR|KR|KRA|CRA\.|KRA\.|CARRERRA|CARREA|K|CARREAR|ARRERA|CARREARA|CARRRERA|CARERRA|CARERA|CCARRERA|CARREREA|KARRERA|CRR|CRRERA|CARRERAR|CASRRERA|CARRREA|CAARRERA|CR\.|KA|CERRERA|CARRERQA|CARR|CQARRERA|CARRER|CARERAR" : "Carrera",
    u"CALLE|CL|CLL|CL\.|CALE|CALL|CALLEL|CALLOE|CLLE|CALLLE|ALLE|CELLE|CCALLE|CLL\.|CALKLE|CALLR|CALLEM" : u"Calle",
    u"DIAGONAL|DG|DIAG|DIAG\.|DGN|DIAGOMAL|DIAGNNAL|DIOGONAL|DIAGOANAL|DAIGONAL|DIG" : u"Diagonal",
    u"TRANSVERSAL|TR|TRANS|TV|TRAV|TRV|TRANSV\.|TRANSVEERSAL|TRA|TRANSV|TRASVERSAL|TRANVERSAL|TRANSVARSAL|TRANSVVERSAL|TRASV|TRANAVERSAL|TRRANSVERSAL|TRASNVERSAL|TRNASVERSAL|TRV\." : u"Transversal",
    u"AVENIDA|AV\.|AV|AVDA|AVE" : u"Avenida",
    u"TRONCAL|TROCAL" : u"Troncal",
    u"AUTOPISTA|AUTOPISTE|AUT\." : u"Autopista",
    u"VÍA|VIA" : u"vía",
    u"DESVÍO|DESVIO|DEVIO" : u"Desvío",
    u"CIRCULAR|CIRULAR" : u"Circular",
        }
    applychanges(
        conn,
        client,
        replacements,
        "SELECT count(*) as cant FROM ways WHERE tags ?& Array['highway','name'] AND tags -> 'name' ~* '^({0}) .*';",
        "SELECT 1, id FROM ways WHERE tags ?& Array['highway','name'] AND tags -> 'name' ~* '^({1}) .*';",
        "SELECT kmeans(ARRAY[ST_X(l.p), ST_Y(l.p)], {0}) OVER (), l.id, l.name FROM (SELECT id,tags -> 'name' AS name, ST_PointN(linestring,1) AS p FROM ways WHERE tags ?& Array['highway','name'] AND tags -> 'name' ~* '^({1}) .*') AS l ORDER BY kmeans,name;",
        fixstreetname,
        u"Fixing Street Names",)

def fixmunicipalityattribution(oldw,updw,replacement):
    updw[u'tag'][u'source'] = replacement
    return updw

def fixmunicipalitiesattribution():
    replacements = {
        "6" : "SIMCI-ONUDC, con modificaciones por OCHA",
        "4" : "SIMCI-ONUDC, con modificaciones por OCHA",
        }
    applychanges(
        conn,
        client,
        replacements,
        "SELECT count(id) FROM ways WHERE tags ?& Array['admin_level','boundary'] AND tags -> 'admin_level' = '{0}' AND tags -> 'source' = 'OCHA - SIGOT'",
        "SELECT 1,id FROM ways WHERE tags ?& Array['admin_level','boundary'] AND tags -> 'admin_level' = '{0}' AND tags -> 'source' = 'OCHA - SIGOT'",
        "SELECT kmeans(ARRAY[ST_X(l.p), ST_Y(l.p)], {0}) OVER (), l.id, l.name FROM (SELECT id, tags -> 'name' AS name, ST_PointN(linestring,1) AS p  FROM ways WHERE tags ?& Array['admin_level','boundary'] AND tags -> 'admin_level' = '{1}' AND tags -> 'source' = 'OCHA - SIGOT') AS l ORDER BY kmeans,name;",
        fixmunicipalityattribution,
        u"Fixing Municipality and Department Attribution source",
        )

#fixmunicipalitiesattribution()
fixwaynames()
