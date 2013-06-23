osmhelpertools
==============

Tools to fix OSM Data.

The following tools are provided to help with OSM
 * geocoder : Geocoder for Colombia
 * botika : bot to fix things related to Colombia
 * colombiahelper : tools that help people to fix data



Work to be done
===============

[] Gecoder
  [X] Show results in map
  [X] Remove too close results
  [X] Remove results that share the same name, example Carrera 5 in Bogotá
  [X] Show results on right
  [X] Click on results zoom to place
  [X] Popup shows the incoming value
  [] Add city to resulting address
    [X] Generar tablas de poblaciones
    [X] En el momento de crear la información de redis, colocar al final la ciudad
    [X] Paralelización de proceso de ciudad más cercana
    [X] Proyectar resultados
  [] Integrate a parser for humans
  [] CSS love

[] Reverse Geocoder
    [] php to python stored procedure
       [X] Returns the possible interesection name
       [X] Returns a set of intersections with latitude longitude
       [] Find the closest with respect to 0 City
       [] Find distance along the line
    [X] Show fields in map to reverse geocoding
    [X] Click shows the name
    [] Return a better structure
    [] Store in a table failed reverse geocodings - Requires better update
    [] Store in a table failed geocoding - Requires better update

[X] Helper tools
  [] Show ways whose name is missing
    [] Requires zoom level to change according to map browse
    [] Find totals

[] Smarter update process
  [] Drop tables instead of database

[] Gamification
  [] Login related to OSM
  [] If you help, you can use some tools
  [] Table points
    [] You are registered
    [] You have edited recently
    [] You have edited
    [] You have uploaded a trace
    [] You have uploaded a trace recently
    [] You are XXXXXX
    [] You created an entry diary
    [] You created an entry diary
    [] You are registered in talk-co
    [] You have closed notes
    [] You have closed notes recently
