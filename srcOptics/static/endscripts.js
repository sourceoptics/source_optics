function detailView(e) {
    console.log(e.target.innerHTML);
}

document.querySelectorAll('.repo').forEach(function(e) {
    e.addEventListener('click', detailView);
});

// Sets default start date back a week
var start = document.querySelector('#range .start');
if(!start.value) {
    now = new Date();
    now.setDate(now.getDate() - 7);
    start.value = now.toISOString().split('T')[0];
}
