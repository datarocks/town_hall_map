document.getElementById("load_time").innerHTML = "Latest load: "+geoJsonData.properties.latestLoad;

var stateFips = {
       "01": "Alabama",
       "02": "Alaska",
       "04": "Arizona",
       "05": "Arkansas",
       "06": "California",
       "08": "Colorado",
       "09": "Connecticut",
       "10": "Delaware",
       "11": "District of Columbia",
       "12": "Florida",
       "13": "Geogia",
       "15": "Hawaii",
       "16": "Idaho",
       "17": "Illinois",
       "18": "Indiana",
       "19": "Iowa",
       "20": "Kansas",
       "21": "Kentucky",
       "22": "Louisiana",
       "23": "Maine",
       "24": "Maryland",
       "25": "Massachusetts",
       "26": "Michigan",
       "27": "Minnesota",
       "28": "Mississippi",
       "29": "Missouri",
       "30": "Montana",
       "31": "Nebraska",
       "32": "Nevada",
       "33": "New Hampshire",
       "34": "New Jersey",
       "35": "New Mexico",
       "36": "New York",
       "37": "North Carolina",
       "38": "North Dakota",
       "39": "Ohio",
       "40": "Oklahoma",
       "41": "Oregon",
       "42": "Pennsylvania",
       "44": "Rhode Island",
       "45": "South Carolina",
       "46": "South Dakota",
       "47": "Tennessee",
       "48": "Texas",
       "49": "Utah",
       "50": "Vermont",
       "51": "Virginia",
       "53": "Washington",
       "54": "West Virginia",
       "55": "Wisconsin",
       "56": "Wyoming"
    }

var tiles = L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png', {
			maxZoom: 18,
			attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
		});
		var map = L.map('map');
		L.tileLayer.provider('Stamen.Toner').addTo(map);
		L.control.geocoder('mapzen-YiQFJPe').addTo(map);
		//this gets us legislative districts from the census
		var districtLayer = L.esri.featureLayer({
         url: "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Legislative/MapServer/0",
         simplifyFactor: 0.35,
         precision: 5,
         style: {
            color: '#A9A9A9',
             weight: 1
         }
         }).addTo(map)
         districtLayer.once("load", function(){
         districtLayer.bringToBack();
            });

        districtLayer.bindPopup(function (evt) {
        return L.Util.template('<p>'+ stateFips[evt.feature.properties.STATE]+ '<br> {NAME} </p>', evt.feature.properties);
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