#!/usr/bin/env python
# -*- coding: utf-8 -*-
import psycopg2
import psycopg2.extensions
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash, jsonify

from vectorformats.Feature import Feature
from vectorformats.Formats import GeoJSON

# configuration
#DATABASE = 'postgresql://osm:osm@localhost/osm'
DATABASE="dbname='{0}' user='{1}' host='{2}' password='{3}'".format("osm","osm","localhost","osm")
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)

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
    g.db.execute("SELECT count(*) AS cant,initial AS name FROM ways_to_fix GROUP BY 2 ORDER BY cant DESC,initial")
    entries = [{'cant': row[0], 'name': row[1].capitalize() if row[1]!=u'' else u'Varios'} for row in g.db.fetchall()]
    return render_template('show_entries.html', entries=entries)

@app.route('/show/<initial>')
def show_details(initial):
    q = "SELECT id,name,st_asgeojson(linestring) FROM ways_to_fix WHERE initial='{0}'".format(initial.upper())
    g.db.execute(q)
    details = [Feature(f[0],f[2],{'name' : f[1]}) for f in g.db.fetchall()]
    geoj = GeoJSON.GeoJSON()    
    return jsonify(result=geoj.encode(details).replace("\\",""))

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
    app.run()

