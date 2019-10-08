
function queryStringToJSON() {
    var pairs = location.search.slice(1).split('&');

    var result = {};
    pairs.forEach(function(pair) {
        pair = pair.split('=');
        result[pair[0]] = decodeURIComponent(pair[1] || '');
    });

    return JSON.parse(JSON.stringify(result));
}

var query_string_json = queryStringToJSON();
var query_params = [];
var query_string = "?"

function pickDates(){
    // reload the page w/ the new dates
    query_string_json.start = $("#datepicker_start").val();
    query_string_json.end = $("#datepicker_end").val();
    for (query in query_string_json){ 
        query_params.push(query+"="+ query_string_json[query]);
    }
    query_string += query_params.join("&")
    location.href= window.location.href.split('?')[0]+query_string;
}

function setupDatePicker(datepicker_cal, datepicker_hiddenfield){
        $(datepicker_cal).datepicker({
            format: "yyyy-mm-dd",
            todayBtn: "linked",
            startDate: new Date('1970-01-01T00:00:00'),
            endDate: new Date(Date.now())
        });
        $(datepicker_hiddenfield).val(
            $(datepicker_cal).datepicker('getFormattedDate')
        );

        $(datepicker_cal).on('changeDate', function() {
            $(datepicker_hiddenfield).val(
                $(datepicker_cal).datepicker('getFormattedDate')
            );
        });
};

setupDatePicker('#datepicker_start_cal', '#datepicker_start');
setupDatePicker('#datepicker_end_cal', '#datepicker_end');

$( "#datepicker_dates__display" ).click(function() {
    $("#datepicker_modal").slideToggle("slow");
});

$( "#cancelButton" ).click(function() {
    $( "#datepicker_modal" ).slideToggle("fast");
    // reset the calendar values if user cancels out of datepicker_modal using the value of their corresponding date_display value
    $('#datepicker_start_cal').datepicker('update', $('#start_date_display').attr('data-date'));
    $('#datepicker_end_cal').datepicker('update', $('#end_date_display').attr('data-date'));
});


