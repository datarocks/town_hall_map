



var example_thing = {
        "address": ",  ,   ",
        "date": "Thursday, February 23, 2017",
        "date8061": "2017-02-23",
        "district": "NJ-3",
        "location": " ",
        "meetingType": "Tele-Town Hall",
        "member": "Tom MacArthur",
        "notes": "Ask the Congressman on WOBM 92.7. Call in 732-237-9626\n",
        "party": "Republican",
        "state": "New Jersey",
        "time": "7:00 PM EST"
    }


$(function() {
    $.each(nonGeoData, function(i, item) {
        var $tr = $('<tr>').append(
            $('<td>').text(item.member),
            $('<td>').text(item.state),
            $('<td>').text(item.district),
            $('<td>').text(item.party),
            $('<td>').text(item.meetingType),
            $('<td>').text(item.date),
            $('<td>').text(item.time),
            $('<td class="table-notes">').html(item.notes),
            $('<td>').text(item.location),
            $('<td>').text(item.address)
        ).appendTo('#no_location_table');
        //console.log($tr.wrap('<p>').html());
    });
});