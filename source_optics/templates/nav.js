$(document).ready(function() {

var navBar =`
<button type="button" id="homeButton" class="btn btn-outline-secondary btn-sm">Home &gt;</button>
{% if org %}
<button type="button" id="reposButton" class="btn btn-outline-secondary btn-sm">Org: {{ org.name }} &gt;</button>
{% endif %}
{% if repo and not multiple_repos_selected %}
<button type="button" id="repoButton" class="btn btn-outline-secondary btn-sm">Repo: {{ repo.name }} &gt;</button>
{% endif %}
{% if author %}
<button type="button" id="authorButton" class="btn btn-outline-secondary btn-sm">Author: {{ author.email }} &gt;</button>
{% endif %}
&nbsp;
&nbsp;
{% if repo or repos_str or author %}
{% if not author %}
{% comment %}
author graphs across all repos are coming soon
{% endcomment %}
<button type="button" id="graphsButton" class="btn btn-outline-info btn-sm">Graph</button>
{% endif %}
{% if not multiple_repos_selected %}
<button type="button" id="statsButton" class="btn btn-outline-info btn-sm">Stats</button>
<button type="button" id="feedButton" class="btn btn-outline-info btn-sm">Commit Feed</button>
{% if not author %}
<button type="button" id="filesButton" class="btn btn-outline-info btn-sm">Files</button>
{% endif %}
{% endif %}
{% endif %}
{% if org and not repo and not author %}
<button type="button" id="repoCompareGraphsButton" class="btn btn-outline-info btn-sm">Graph Selected</button>
{% endif %}
`;

$('#navBar').html(navBar);
$('#homeButton').click(function() {
   window.location.href = "/";
});

{% if org %}

  $('#reposButton').click(function() { window.location.href = "/org/{{ org.pk }}/repos"; });

{% endif %}

{% if author %}

  $('#authorButton').click(function() { window.location.href = "/author/{{ author.pk }}"; });
  $('#graphsButton').click(function()  { window.location.href = "/graphs?author={{ author.pk }}&start={{ start_str}}&end_str={{ end_str }}"; });
  $('#feedButton').click(function()   { window.location.href = "/report/commits?author={{ author.pk }}&start={{ start_str}}&end_str={{ end_str }}"; });
  $('#statsButton').click(function()  { window.location.href = "/report/stats?author={{ author.pk }}&start={{ start_str}}&end_str={{ end_str }}"; });

{% elif repo and not multiple_repos_selected %}

  $('#repoButton').click(function()   { window.location.href = "/repo/{{ repo.pk }}"; });
  $('#graphsButton').click(function()  { window.location.href = "/graphs?repo={{ repo.pk }}&start={{ start_str}}&end_str={{ end_str }}"; });
  $('#feedButton').click(function()   { window.location.href = "/report/commits?repo={{ repo.pk }}&start={{ start_str}}&end_str={{ end_str }}"; });
  $('#statsButton').click(function()  { window.location.href = "/report/stats?repo={{ repo.pk }}&start={{ start_str}}&end_str={{ end_str }}"; });

{% elif repos_str %}

  $('#graphsButton').click(function() { window.location.href = "/graphs?repos={{ repos_str }}&start={{ start_str}}&end_str={{ end_str }}"; });

{% endif %}

{% if org and not repo and not author %}
  $('#repoCompareGraphsButton').click(function() {
      var repos = [];
      $.each($("input[name='repo']:checked"), function(){
          repos.push($(this).val());
      });
      var repos_str = repos.join("+");
      var new_url = "/graphs?org={{ org.pk }}&repos=" + repos_str + "&start={{ start_str }}&end={{ end_str}}";
      if (repos.length) {
          window.location.href = new_url
      }
  });
{% endif %}

{% comment %}
FIXME: disable the button instead and grey-out. DRY.
{% endcomment %}
{% if mode == 'stats' %}
   var text = $('#statsButton').text()
   $('#statsButton').text("*" + text)
{% elif mode == 'graphs' %}
   var text = $('#graphsButton').text()
   $('#graphsButton').text("*" + text)
{% elif mode == 'feed' %}
   var text = $('#feedButton').text()
   $('#feedButton').text("*" + text)
{% elif mode == 'orgs' %}
   var text = $('#orgsButton').text()
   $('#orgsButton').text("*" + text )
{% elif mode == 'repos' %}
   var text = $('#reposButton').text()
   $('#reposButton').text("*" + text)
{% elif mode == 'author' %}
   var text = $('#authorButton').text()
   $('#authorButton').text("*" + text)
{% elif mode == 'repo' %}
   var text = $('#repoButton').text()
   $('#repoButton').text("*" + text)
{% elif mode == 'files' %}
   var text = $('#filesButton').text()
   $('#filesButton').text("*" + text)
{% endif %}


});