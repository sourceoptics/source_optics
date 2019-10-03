
// Instantiate datepicker - start date
//=====================================
$('#datepicker_start_cal').datepicker({
    format: "yyyy-mm-dd",
    todayBtn: "linked",

});
// Set initial value of start date hidden field
$('#datepicker_start').val(
    $('#datepicker_start_cal').datepicker('getFormattedDate')
);
// Set initial value of start date display
$('#start_date_display').text(
    dateToString(
        $('#start_date_display').text()
    )
);
// Modify the value of start date hidden field
$('#datepicker_start_cal').on('changeDate', function() {
    $('#datepicker_start').val(
        $('#datepicker_start_cal').datepicker('getFormattedDate')
    );
});

// Instantiate datepicker - end date
//===================================
$('#datepicker_end_cal').datepicker({
    format: "yyyy-mm-dd",
    todayBtn: "linked",

});
// Set initial value of end date hidden field and display value
$('#datepicker_end').val(
    $('#datepicker_end_cal').datepicker('getFormattedDate')
);
// Set initial value of end date display
$('#end_date_display').text(
    dateToString(
        $('#end_date_display').text()
    )
);
// Modify the value of end date hidden field and display value
$('#datepicker_end_cal').on('changeDate', function() {
    $('#datepicker_end').val(
        $('#datepicker_end_cal').datepicker('getFormattedDate')
    );
});

$( "#datepicker_dates__display" ).click(function() {
    $( "#myModal" ).slideToggle(
        "slow", "swing");
});
$( "#cancelButton" ).click(function() {
    $( "#myModal" ).slideToggle(
        "fast", "swing"
        );

    // Reset the calendar values
    $('#datepicker_start_cal').datepicker('update', 
        $('#start_date_display').attr('data-date')
    );
    $('#datepicker_end_cal').datepicker('update', 
        $('#end_date_display').attr('data-date')
    );
});

// Date string converter / formatter
function dateToString(date_string){
    var d = new Date(date_string)
    var [day, month, year] = d.toUTCString().split(" ").slice(1,4)
    return month + " " + day + ", " + year
}
