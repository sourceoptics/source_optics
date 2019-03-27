/**
 * @file 
 * Provides additional tweaks to front-end components
 *
 * These additional scripts are intended to be run at the end
 * of the document after all elements have been rendered
 */

/** Set default start date back one week from current
 * date on #range .start input element
 */
var start = document.querySelector('#range .start');
if(!start.value) {
    now = new Date();
    now.setDate(now.getDate() - 7);
    start.value = now.toISOString().split('T')[0];
}

/**
 * Sets location targets to .switch input elements 
 * based on data-on/off attributes
 */
document.querySelectorAll('.switch input').forEach(function(sw) {
    sw.onchange = function () {
        if(sw.checked) {
            setTimeout(function(){ window.location = sw.dataset.on; }, 400);
        } else {
            setTimeout(function(){ window.location = sw.dataset.off; }, 400);
        }
    };
});



// document.querySelectorAll('.repo').forEach(function(e) {
//     e.addEventListener('click', function() {
//         if(this.classList.contains('expand')) {
//             this.classList.remove('expand');
//         } else {
//             this.classList.add('expand');
//             var template = `
//                 <div class='details'>
//                     ${this.innerHTML}
//                 </div>
//             `;
//             this.parentElement.insertAdjacentHTML('afterend', template);
//         }
//     });
// });