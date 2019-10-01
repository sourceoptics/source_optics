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
    query_string_json.start = $("#datepicker_start").val();
    query_string_json.end = $("#datepicker_end").val();
    for (query in query_string_json){ 
        query_params.push(query+"="+ query_string_json[query]);
    }
    query_string += query_params.join("&")
    location.href= window.location.href.split('?')[0]+query_string;
}