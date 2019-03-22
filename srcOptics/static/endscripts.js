document.querySelectorAll('.repo').forEach(function(e) {
    e.addEventListener('click', function() {
        if(this.classList.contains('expand')) {
            this.classList.remove('expand');
        } else {
            this.classList.add('expand');
            var template = `
                <div class='details'>
                    ${this.innerHTML}
                </div>
            `;
            this.parentElement.insertAdjacentHTML('afterend', template);
        }
    });
});

// Sets default start date back a week
var start = document.querySelector('#range .start');
if(!start.value) {
    now = new Date();
    now.setDate(now.getDate() - 7);
    start.value = now.toISOString().split('T')[0];
}
