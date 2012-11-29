Requirements
============

* Internet connection
* osm2pgsql
* wget
* bunzip2
* Postgresql9.1 with hstore EXTENSION and Postgis support(1.5.3 tested)
* osmosis 0.4.0
* redis2.4
* redis-py

You will be comfortable with a Debianized Linux distro

Usage
=====

copy localinfo.sh.sample into localinfo.sh and modify the variables to
suit your installation.  Please note that due to osmosis we can not
use a database in another port and we must use postgres user to
import data.  Sorry for this.

With this you will only have the database prepared to use the real application
to geocode.   openstreetblock, grab it at your nearest github provider(https://github.com/fruminator/openstreetblock)

What you get
============

* A table in postgresql with way intersections
* A database in redis to fetch data quickly to get geocoding
