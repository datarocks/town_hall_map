document.getElementById("load_time").innerHTML = "Latest load: "+geoJsonData.properties.latestLoad;


var tiles = L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png', {
			maxZoom: 18,
			attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
		});
		var map = L.map('map');
		L.tileLayer.provider('Stamen.Toner').addTo(map);
		//this gets us legislative districts from the census
		var districtLayer = L.esri.featureLayer({
         url: "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Legislative/MapServer/0",
         simplifyFactor: 0.35,
         precision: 5
         }).addTo(map)
         districtLayer.once("load", function(){
         districtLayer.bringToBack();
            });

		var markers = L.markerClusterGroup({maxClusterRadius: 5, spiderfyDistanceMultiplier:2 });

		function getValue(x) {
	        return x == "Republican" ? "#ff0000" :
	       x == "Democratic" ? "#0000ff" :
		       "#FFEDA0";
}
        function setPopupValue(feature, layer) {
            var popupText = "Party: " + feature.properties.party
                + "<br>Member: " + feature.properties.member
                + "<br>District: " + feature.properties.district
                + "<br>State: " + feature.properties.state
                + "<br>Meeting Type: " + feature.properties.meetingType
                + "<br>Location: " + feature.properties.location
                + "<br>Address: " + feature.properties.address
                + "<br>Date: " + feature.properties.date
                + "<br>Time: " + feature.properties.time
                + "<br>Notes: " + feature.properties.notes;
            layer.bindPopup(popupText);
            }

		var geoJsonLayer = L.geoJson(geoJsonData, {
			pointToLayer: function (feature, latlng) {
        	return L.circleMarker(latlng, {
            radius: 6,
            fillColor: getValue(feature.properties.party),
            color: "#000",
            weight: 1,
            opacity: 1,
            fillOpacity: 0.8
            });
        	},
			onEachFeature: setPopupValue

		});
		markers.addLayer(geoJsonLayer);
		map.addLayer(markers);

		map.fitBounds(markers.getBounds());