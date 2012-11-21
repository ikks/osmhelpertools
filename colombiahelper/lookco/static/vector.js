var map;
var waystofix;
var hireslayer;

String.prototype.format = function() {
    var formatted = this;
    for (var i = 0; i < arguments.length; i++) {
        var regexp = new RegExp('\\{'+i+'\\}', 'gi');
        formatted = formatted.replace(regexp, arguments[i]);
    }
    return formatted;
};

function showInfo(feature) {
    $("#info_detail").html('{0} [ <a href="http://www.openstreetmap.org/?mlat={1}&mlon={2}&zoom=17" target="_blank">Ver</a> | <a href="http://www.openstreetmap.org/edit?lat={1}&lon={2}&zoom=17" target="_blank">Editar</a> | <a href="http://www.openstreetmap.org/edit?editor=remote&lat={1}&lon={2}&zoom=17">JOSM</a> ]'.format(feature.data.name,feature.data.middle.coordinates[1],feature.data.middle.coordinates[0]));
}

function colorize(feature){
    $(".hiresitem p").css("background-color","");
    $("td[data-hiresid='" + feature.fid + "'] p").css("background-color","#CCFFCC");
}


function init() {
    map = new OpenLayers.Map({
        div: "map",
        projection: new OpenLayers.Projection("EPSG:900913"),
        units: "m",
        maxResolution: 156543.0339,
        maxExtent: new OpenLayers.Bounds(
            -20037508, -20037508, 20037508, 20037508.34
        )
    });
    
    var osm = new OpenLayers.Layer.OSM();

    var styleMap = new OpenLayers.StyleMap({
      'strokeWidth': 5,
      'strokeColor': '#FF0000'
    });
    waystofix = new OpenLayers.Layer.Vector("Vías Nombres raros",{styleMap: styleMap});
    
    var styleMaphires = new OpenLayers.StyleMap({
      'strokeWidth': 2,
      'strokeColor': '#00AA00',
      'fillColor': '#AAFFAA',
    });
    hireslayer = new OpenLayers.Layer.Vector("Aerofotografía para calcar",{styleMap: styleMaphires});
    
    var options = {
        hover: true,
        onSelect: showInfo
    };
    var select = new OpenLayers.Control.SelectFeature(waystofix, options);
    map.addControl(select);
    select.activate();

    var other = {
        hover: true,
        onSelect: colorize,
    };

    var colorthis = new OpenLayers.Control.SelectFeature(hireslayer, other);
    map.addControl(colorthis);
    colorthis.activate();

    var layers = [osm, waystofix, hireslayer];
    map.addLayers(layers);

    // map.addControl(new OpenLayers.Control.LayerSwitcher());

    map.setCenter(
        new OpenLayers.LonLat(-74.11128,4.61799).transform(
            new OpenLayers.Projection("EPSG:4326"),
            map.getProjectionObject()
        ), 
        5
    );
    map.addControl(new OpenLayers.Control.MousePosition({displayProjection 
         :new OpenLayers.Projection("EPSG:4326")
    }));

    $("#goto").click(function() {
    map.moveTo(
        new OpenLayers.LonLat(-74.11128,4.61799).transform(
            new OpenLayers.Projection("EPSG:4326"),
            map.getProjectionObject()
        ), 5)
    });
    $.get("/hires/",function(result){
        var coder = new OpenLayers.Format.GeoJSON({
            'internalProjection': map.baseLayer.projection,
            'externalProjection': new OpenLayers.Projection("EPSG:4326")
        })
        var features = coder.read(result);
        var bounds;
        if(features) {
            if(features.constructor != Array) {
                features = [features];
            }
            for(var i=0; i<features.length; ++i) {
                if (!bounds) {
                    bounds = features[i].geometry.getBounds();
                } else {
                    bounds.extend(features[i].geometry.getBounds());
                }

            }
            hireslayer.addFeatures(features);
        } 
        else {
            console.log('Server error ' + type);
        }
    });
    waystofix.setVisibility(false);
}
