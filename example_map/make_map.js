var tiles = L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png', {
			maxZoom: 18,
			attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
		});
		var map = L.map('map')
				.addLayer(tiles);
		var markers = L.markerClusterGroup({maxClusterRadius: 5});
		var geojsonMarkerOptions = {
            radius: 8,
            fillColor: "#ff7800",
            color: "#000",
            weight: 1,
            opacity: 1,
            fillOpacity: 0.8
            };

		var geoJsonLayer = L.geoJson(geoJsonData, {
			pointToLayer: function (feature, latlng) {
        	return L.circleMarker(latlng, geojsonMarkerOptions);
        	},
			onEachFeature: function (feature, layer) {
				layer.bindPopup(feature.properties.party
				);
			}
		});
		markers.addLayer(geoJsonLayer);
		map.addLayer(markers);
		map.fitBounds(markers.getBounds());