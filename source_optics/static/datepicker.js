function QueryStringToJSON() {            
    var pairs = location.search.slice(1).split('&');
    
    var result = {};
    pairs.forEach(function(pair) {
        pair = pair.split('=');
        result[pair[0]] = decodeURIComponent(pair[1] || '');
    });

    return JSON.parse(JSON.stringify(result));
}

var query_string_json = QueryStringToJSON();
var query_params = [];
var query_string = "?"

function pickDates(){
    // Take the start and end values from their respective inline-datepicker's
    // hidden field, create a new query with said values and make a new request.
    query_string_json.start = $("#datepicker_start").val();
    query_string_json.end = $("#datepicker_end").val();
    for (query in query_string_json){ 
        query_params.push(query+"="+ query_string_json[query]);
    }
    query_string += query_params.join("&")
    location.href= window.location.href.split('?')[0]+query_string;
}

function instantiateAndSetupDatepicker(
    datepicker_cal, 
    datepicker_hiddenfield,
    ){
        // Instantiate datepicker
        $(datepicker_cal).datepicker({
            format: "yyyy-mm-dd",
            todayBtn: "linked",
            startDate: new Date('1970-01-01T00:00:00'),
            // NOTE: endDate below is changing date to tomorrow to take
            // into account the following code from the scope.py view --> 
            // self.end = end + datetime.timedelta(days=1)  # start of tomorrow
            // <--
            // This may be confusing for the user when they see that their end date
            // selection has changed to + 1 day. Although this is necessary
            // on the backend to select data that's included on that end date, 
            // maybe end_str can retain the selected end date instead of reflecting
            // the + 1 day timedelta.
            endDate: new Date(Date.now() + 86400000)
        });
        // Set initial value of start date hidden field
        $(datepicker_hiddenfield).val(
            $(datepicker_cal).datepicker('getFormattedDate')
        );
};

function modifyDatepickerHiddenFieldVal(
    datepicker_cal, 
    datepicker_hiddenfield,
    ){
        $(datepicker_cal).on('changeDate', function() {
            $(datepicker_hiddenfield).val(
                $(datepicker_cal).datepicker('getFormattedDate')
            );
        });
};

// Instantiate datepicker - start date
//=====================================
instantiateAndSetupDatepicker(
    '#datepicker_start_cal', 
    '#datepicker_start', 
    '#start_date_display',
);

// Modify the value of start date hidden field
modifyDatepickerHiddenFieldVal(
    '#datepicker_start_cal', 
    '#datepicker_start',
);

// Instantiate datepicker - end date
//===================================
instantiateAndSetupDatepicker(
    '#datepicker_end_cal', 
    '#datepicker_end', 
    '#end_date_display',
);

// Modify the value of end date hidden field and display value
modifyDatepickerHiddenFieldVal(
    '#datepicker_end_cal', 
    '#datepicker_end',
);


// toggles the #datepicker_modal when clicking #datepicker_dates__display
$( "#datepicker_dates__display" ).click(function() {
    $( "#datepicker_modal" ).slideToggle("slow");
});

// Closes the datepicker_modal and resets the calendar vals
$( "#cancelButton" ).click(function() {
    $( "#datepicker_modal" ).slideToggle("fast");

    // Resets the calendar values if user cancels out of datepicker_modal
    // using the value of their corresponding date_display value
    $('#datepicker_start_cal').datepicker('update', 
        $('#start_date_display').attr('data-date')
    );
    $('#datepicker_end_cal').datepicker('update', 
        $('#end_date_display').attr('data-date')
    );
});


