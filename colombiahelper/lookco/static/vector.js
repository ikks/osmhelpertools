var map;
var waystofix;
var hireslayer;
var manynameslayer;
var geocoderresults;

String.prototype.format = function() {
    var formatted = this;
    for (var i = 0; i < arguments.length; i++) {
        var regexp = new RegExp('\\{'+i+'\\}', 'gi');
        formatted = formatted.replace(regexp, arguments[i]);
    }
    return formatted;
};

OpenLayers.Control.Click = OpenLayers.Class(OpenLayers.Control, {                
    defaultHandlerOptions: {
        'single': true,
        'double': false,
        'pixelTolerance': 0,
        'stopSingle': false,
        'stopDouble': false
    },

    initialize: function(options) {
        this.handlerOptions = OpenLayers.Util.extend(
            {}, this.defaultHandlerOptions
        );
        OpenLayers.Control.prototype.initialize.apply(
            this, arguments
        ); 
        this.handler = new OpenLayers.Handler.Click(
            this, {
                'click': this.trigger
            }, this.handlerOptions
        );
    }, 

    trigger: function(e) {
        var lonlat = map.getLonLatFromViewPortPx(e.xy);
        var lonlat = map.getLonLatFromViewPortPx(e.xy).transform(
            map.getProjectionObject(),
            new OpenLayers.Projection("EPSG:4326")
        );
        var calculated = ""
        switch($("#id_dothis").val()){
            case "marker":
                calculated = "http://www.openstreetmap.org/?mlat={0}&mlon={1}&zoom=18&layers=M\n".format(
                    lonlat.lat.toFixed(5),
                    lonlat.lon.toFixed(5)
                );
                break;
            case "simple":
                calculated = lonlat.lat.toFixed(5) + "," + lonlat.lon.toFixed(5)+"\n";
                break;
            case "wkt":
                calculated = "ST_GeomFromText('POINT({0} {1})',4326)\n".format(
                    lonlat.lon.toFixed(5),
                    lonlat.lat.toFixed(5)
                );
                break;
            case "inversegeo":
                $.post("/inversegeocoder", { lat: lonlat.lat.toFixed(7), lon: lonlat.lon.toFixed(7)}, function(incoming){
                    if(typeof(incoming) !== "string"){
                        result = incoming[0] + "\n";
                        if (result.indexOf("#") === -1){
                            calculated = result;
                        }
                        else{
                            pair = result.split('#')
                            if (pair[1].length == 0)
                                calculated = pair[0] + "\n";
                            else if (pair[1].indexOf(",") === -1){
                                calculated = result;
                            }
                            else {
                                compl = pair[1].split(',');
                                calculated = "{0} entre {1} y {2}".format(pair[0], compl[0], compl[1])
                            }
                        }
                    }
                    $("#thearea").append(calculated);
                })
                break;
        }
        $("#thearea").append(calculated);
    }

});

function showInfo(feature) {
    $("#info_detail").html('{0} [ <a href="http://www.openstreetmap.org/?mlat={1}&mlon={2}&zoom=17" target="_blank">Ver</a> | <a href="http://www.openstreetmap.org/edit?lat={1}&lon={2}&zoom=17" target="_blank">Editar</a> | <a href="http://www.openstreetmap.org/edit?editor=remote&lat={1}&lon={2}&zoom=17">JOSM</a> ]'.format(feature.data.name,feature.data.middle.coordinates[1],feature.data.middle.coordinates[0]));
}

function colorize(feature){
    $(".hiresitem p").css("background-color","");
    $("td[data-hiresid='" + feature.fid + "'] p").css("background-color","#CCFFCC");
}

function showthing(myfilter) {
    $.get("/show/"+myfilter,function(result){
        $("#feature_name").html(myfilter);
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
            waystofix.removeAllFeatures();
            waystofix.addFeatures(features);
            map.zoomToExtent(bounds);
            var plural = (features.length > 1) ? 's' : '';
        } else {
            console.log('Server error getting names with suspicious name' + type);
        }
    });
    return false;
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
    waystofix = new OpenLayers.Layer.Vector("Vías Nombres raros", {styleMap: styleMap});
    
    var styleMaphires = new OpenLayers.StyleMap({
      'strokeWidth': 2,
      'strokeColor': '#00AA00',
      'fillColor': '#AAFFAA',
    });
    hireslayer = new OpenLayers.Layer.Vector("Aerofotografía para calcar",{styleMap: styleMaphires});
    
    var strategy = new OpenLayers.Strategy.Cluster({distance: 15, threshold: 3});
    manynameslayer = new OpenLayers.Layer.Vector("Intersecciones con varios nombres", {strategies: [strategy]});

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

    geocoderresults = new OpenLayers.Layer.Markers("Geo");

    var layers = [osm, waystofix, hireslayer, manynameslayer, geocoderresults];
    map.addLayers(layers);
    manynameslayer.setVisibility(false);
    waystofix.setVisibility(false);
    geocoderresults.setVisibility(false);
    hireslayer.setVisibility(true);

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

    var click = new OpenLayers.Control.Click();
    map.addControl(click);
    click.activate();

    $("#goto").click(function() {
        map.moveTo(
            new OpenLayers.LonLat(-74.11128,4.61799).transform(
                new OpenLayers.Projection("EPSG:4326"),
                map.getProjectionObject()
            ), 5
        );
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
            console.log('Server error for hires ' + type);
        }
    });

    $.get("/intersections/", function(result){
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
            manynameslayer.addFeatures(features);
        } 
        else {
            console.log('Server error for intersections' + type);
        }
    });


}
