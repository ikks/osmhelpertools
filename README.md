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
       [] Returns a set of intersections with latitude longitude
       [] Find the closest with respect to 0 City
       [] Find distance along the line
    [] Show fields in map to reverse geocoding
    [] Click shows the name
    [] A free ride with some points



