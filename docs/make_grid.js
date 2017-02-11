// this example has items declared globally. bad javascript. but keeps the example simple.

var columnDefs = [
    {headerName: "Member", field: "member", },
    {headerName: "Party", field: "party"},
    {headerName: "District", field: "district"},
    {headerName: "State", field: "state"},
    {headerName: "Date", field: "date"},
    {headerName: "Meeting Type", field: "meetingType"},
    {headerName: "Time", field: "time"},
    {headerName: "Notes", field: "notes"}
];


var gridOptions = {
    columnDefs: columnDefs,
    rowData: nonGeoData,
    autoSizeColumns: true
};

function autoSizeAll() {
    var allColumnIds = [];
    columnDefs.forEach( function(columnDef) {
        allColumnIds.push(columnDef.field);
    });
    gridOptions.columnApi.autoSizeColumns(allColumnIds);
}


// wait for the document to be loaded, otherwise
// ag-Grid will not find the div in the document.
document.addEventListener("DOMContentLoaded", function() {
    var eGridDiv = document.querySelector('#myGrid');
    new agGrid.Grid(eGridDiv, gridOptions);
});



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