function detailView(e) {
    var val = e.toElement.hash.substring(1);
    console.log(val);
}

document.querySelectorAll('.repo').forEach(function(e) {
    e.addEventListener('click', detailView);
});