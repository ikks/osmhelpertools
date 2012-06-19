var map;
var vectors;

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
        var lonlat = map.getLonLatFromViewPortPx(e.xy).transform(
            map.getProjectionObject(),                    new OpenLayers.Projection("EPSG:4326"));
	$.get("http://test.openstreetmap.co/geoc/osb.php?ll="+lonlat.lat.toFixed(5)+","+lonlat.lon.toFixed(5)+"&format=json", function(response){
	    json = eval("(" + response + ')');
	    var diraprox = "";
	    if (json.text !== undefined && json.error === undefined)
		diraprox = " "+json.text;
	    document.getElementById("thearea").value+=lonlat.lat.toFixed(5)+","+lonlat.lon.toFixed(5)+diraprox+"\n";
	});
    }

});

String.prototype.format = function() {
    var formatted = this;
    for (var i = 0; i < arguments.length; i++) {
        var regexp = new RegExp('\\{'+i+'\\}', 'gi');
        formatted = formatted.replace(regexp, arguments[i]);
    }
    return formatted;
};

function showInfo(feature) {
    $("#info_detail").html('{0} [ <a href="http://www.openstreetmap.org/?mlat={1}&mlon={2}&zoom=17" target="_blank">Ver</a> | <a href="http://www.openstreetmap.org/edit?editor=remote&lat={1}&lon={2}&zoom=17">JOSM</a> ]'.format(feature.data.name,feature.data.middle.coordinates[1],feature.data.middle.coordinates[0]));
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
      'strokeColor': '#ff0000'
    });
    vectors = new OpenLayers.Layer.Vector("Vías Nombres raros",{styleMap: styleMap});
    
    var options = {
        hover: true,
        onSelect: showInfo,
    };
    var select = new OpenLayers.Control.SelectFeature(vectors, options);
    map.addControl(select);
    select.activate();

    var layers = [osm, vectors];
    map.addLayers(layers);

    map.addControl(new OpenLayers.Control.LayerSwitcher());

    map.setCenter(
        new OpenLayers.LonLat(-74.11128,4.61799).transform(
            new OpenLayers.Projection("EPSG:4326"),
            map.getProjectionObject()
        ), 
        11
    );
    map.addControl(new OpenLayers.Control.MousePosition({displayProjection 
							 :new OpenLayers.Projection("EPSG:4326")
    }));
    var click = new OpenLayers.Control.Click();
    map.addControl(click);
    click.activate();


    $("#goto").click(function() {
	map.moveTo(
            new OpenLayers.LonLat(-70.00098,-0.91673).transform(
            new OpenLayers.Projection("EPSG:4326"),
            map.getProjectionObject()
        ),3);
    });
}
