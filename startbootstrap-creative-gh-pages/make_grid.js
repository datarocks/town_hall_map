
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