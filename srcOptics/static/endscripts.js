function detailView(e) {
    console.log(e.target.innerHTML);
}

document.querySelectorAll('.repo').forEach(function(e) {
    e.addEventListener('click', detailView);
});

