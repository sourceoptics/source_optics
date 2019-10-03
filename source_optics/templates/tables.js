function authorNav(value) {
   var index = "<a href='/author/" + value + "' aria-label='Index'><i aria-hidden='true' class='fas fa-user' title='Index'></i></a>&nbsp;";
   //var graphs = "<a href='/graphs?author=" + value + "&start={{ start_str }}&end={{ end_str }}&intv={{ intv }}' aria-label='Graphs'><i aria-hidden='true' class='fas fa-chart-line'></i></a>&nbsp;";
   var stats  = "<a href='/report/stats?author=" + value + "&start={{ start_str }}&end={{ end_str }}' aria-label='Statistics'><i aria-hidden='true' class='fas fa-table' title='Stats'></i></a>&nbsp;";
   var commit_feed = "<a href='/report/commits?author=" + value + "&start={{ start_str }}&end={{ end_str }}' aria-label='Commits'><i aria-hidden='true' class='fas fa-rss-square' title='Commits'></i></a>&nbsp;";
   return index + stats + commit_feed; 
}

function repoNav(value) {
   var index = "<a href='/repo/" + value + "' aria-label='Index'><i aria-hidden='true' class='fas fa-database' title='Index'></i></a>&nbsp;";
   var graphs = "<a href='/graphs?repo=" + value + "&start={{ start_str }}&end={{ end_str }}&intv={{ intv }}' aria-label='Graphs'><i aria-hidden='true' class='fas fa-chart-line' title='Graphs'></i></a>&nbsp;";
   var stats  = "<a href='/report/stats?repo=" + value + "&start={{ start_str }}&end={{ end_str }}' aria-label='Statistics'><i aria-hidden='true' class='fas fa-table' title='Stats'></i></a>&nbsp;";
   var commit_feed = "<a href='/report/commits?repo=" + value + "&start={{ start_str }}&end={{ end_str }}' aria-label='Commits'><i aria-hidden='true' class='fas fa-rss-square' title='Commits'></i></a>&nbsp;";
   var files = "<a href='/report/files?repo=" + value + "&start={{ start_str }}&end={{ end_str }}&path=' aria-label='Files'><i aria-hidden='true' class='fas fa-folder-open' title='Files'></i></a>&nbsp;";
   return index + graphs + stats + commit_feed + files;
}
