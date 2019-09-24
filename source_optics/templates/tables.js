function authorNav(value) {
   var index = "<a href='/author/" + value + "'><i class='fas fa-user'></i></a>&nbsp;";
   //var graphs = "<a href='/graphs?author=" + value + "&start={{ start_str }}&end={{ end_str }}&intv={{ intv }}'><i class='fas fa-chart-line'></i></a>&nbsp;";
   var stats  = "<a href='/report/stats?author=" + value + "&start={{ start_str }}&end={{ end_str }}'><i class='fas fa-table'></i></a>&nbsp;";
   var commit_feed = "<a href='/report/commits?author=" + value + "&start={{ start_str }}&end={{ end_str }}'><i class='fas fa-rss-square'></i></a>&nbsp;";
   return index + stats + commit_feed;
}

function repoNav(value) {
   var index = "<a href='/repo/" + value + "'><i class='fas fa-database'></i></a>&nbsp;";
   var graphs = "<a href='/graphs?repo=" + value + "&start={{ start_str }}&end={{ end_str }}&intv={{ intv }}'><i class='fas fa-chart-line'></i></a>&nbsp;";
   var stats  = "<a href='/report/stats?repo=" + value + "&start={{ start_str }}&end={{ end_str }}'><i class='fas fa-table'></i></a>&nbsp;";
   var commit_feed = "<a href='/report/commits?repo=" + value + "&start={{ start_str }}&end={{ end_str }}'><i class='fas fa-rss-square'></i></a>&nbsp;";
   var files = "<a href='/report/files?repo=" + value + "&start={{ start_str }}&end={{ end_str }}&path=/'><i class='fas fa-folder-open'></i></a>&nbsp;";
   return index + graphs + stats + commit_feed + files;
}
