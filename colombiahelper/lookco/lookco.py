#!/usr/bin/env python
# -*- coding: utf-8 -*-
import psycopg2
import psycopg2.extensions
import logging
import simplejson
import redis

from flask import Flask
from flask import request
from flask import session
from flask import g
from flask import redirect
from flask import url_for
from flask import render_template
from flask import flash
from flask import Response

from vectorformats.Feature import Feature
from vectorformats.Formats import GeoJSON

logging.basicConfig(filename='/tmp/map.log', level=logging.INFO)

# configuration
#DATABASE = 'postgresql://osm:osm@localhost/osm'
DATABASE = "dbname='{0}' user='{1}' host='{2}' password='{3}'".format(
    "osm",
    "osm",
    "localhost",
    "osm"
)
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'

app = Flask(__name__)
app.config.from_object(__name__)
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
r_server = redis.Redis("localhost")


def connect_db():
    conn = psycopg2.connect(app.config['DATABASE'])
    return conn.cursor()


@app.before_request
def before_request():
    g.db = connect_db()


@app.teardown_request
def teardown_request(exception):
    g.db.close()


@app.route('/')
def show_entries():
    g.db.execute("SELECT count(*) AS cant,initial AS name FROM ways_to_fix GROUP BY 2  HAVING count(*) < 500 ORDER BY cant DESC,initial")
    entries = [{'cant': row[0], 'name': row[1].capitalize() if row[1] != u'' else u'Varios'} for row in g.db.fetchall()]
    g.db.execute("SELECT id, COALESCE(tags -> 'name', tags -> 'note', tags -> 'description', tags -> 'source', '') AS name, st_asgeojson(linestring) FROM ways WHERE tags ? 'hires' ORDER BY 2;")
    hires = [{'id': row[0], 'desc': row[1]} for row in g.db.fetchall()]
    g.db.execute("SELECT id, count, x(geom), y(geom), names FROM inter_to_fix;")
    intersections = [{'id': row[0], 'desc': row[4], 'lat':row[3], 'lon':row[2]} for row in g.db.fetchall()]
    return render_template(
        'show_entries.html',
        entries=entries,
        hires=hires,
        intersections=intersections
    )


@app.route('/geocoder', methods=['POST'])
def geocoder():
    incoming_dirs = request.form.get('dirs')
    if incoming_dirs is None:
        return ''
    lines = incoming_dirs.split('\n')
    answer = []
    resolved = 0
    count = 0
    for line in lines:
        parsed = line.split('#')
        if len(parsed) != 2:
            continue
        count += 1
        result = {
            'incoming': line,
            'latlon': r_server.hget(*[segment.strip() for segment in parsed]),
        }
        if result['latlon'] is not None:
            resolved += 1
        answer.append(result)
    return Response(
        response=simplejson.dumps({
            'answer': answer,
            'incoming': count,
            'resolved': resolved,
        }),
        status=200,
        mimetype="application/json"
    )


@app.route('/show/<initial>')
def show_details(initial):
    q = "SELECT id,name,st_asgeojson(linestring),st_asgeojson(ST_PointN(linestring,ST_NumPoints(linestring)/2)) AS middle FROM ways_to_fix WHERE initial = %s"
    g.db.execute(q, (initial.upper(),))
    details = [Feature(f[0], simplejson.loads(f[2]), {'name': f[1], 'middle': simplejson.loads(f[3])}) for f in g.db.fetchall()]
    geoj = GeoJSON.GeoJSON()
    return geoj.encode(details)


@app.route('/hires/')
def hires():
    q = "SELECT id, COALESCE(tags -> 'name', tags -> 'note', tags -> 'description', tags -> 'source'), st_asgeojson(linestring) FROM ways WHERE tags ? 'hires' ORDER BY id;"
    g.db.execute(q)
    details = [Feature(f[0], simplejson.loads(f[2]), {'data': f[1]}) for f in g.db.fetchall()]
    geoj = GeoJSON.GeoJSON()
    return geoj.encode(details)


@app.route('/intersections/')
def intersections():
    q = "SELECT id, count, st_asgeojson(geom) FROM inter_to_fix"
    g.db.execute(q)
    details = [Feature(f[0], simplejson.loads(f[2]), {'cant': f[1]}) for f in g.db.fetchall()]
    geoj = GeoJSON.GeoJSON()
    return geoj.encode(details)


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))

if __name__ == '__main__':
    app.run(host='0.0.0.0')
