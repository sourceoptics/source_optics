/**
 * @file 
 * Provides additional tweaks to front-end components
 *
 * These additional scripts are intended to be run at the end
 * of the document after all elements have been rendered
 */

'use strict';

/** Set default start date back one week from current
 * date on #range .start input element
 */
var form = document.getElementById('range');
let start = form.querySelector('.start');
if(!start.value) {
    let now = new Date();
    now.setDate(now.getDate() - 7);
    start.value = now.toISOString().split('T')[0];
}

/**
 * Sets location targets to .switch input elements 
 * based on data-on/off attributes
 */
let switches = document.querySelectorAll('.switch input');
if(switches.length) {
    switches.forEach(function(sw) {
        sw.onchange = function () {
            if(sw.checked) {
                setTimeout(function(){ window.location = sw.dataset.on; }, 400);
            } else {
                setTimeout(function(){ window.location = sw.dataset.off; }, 400);
            }
        };
    });
}


var search = document.querySelector('#search input');
if(search) {
    search.onkeyup = function() {
        if(this.value) {
            let Http = new XMLHttpRequest();
            Http.open('GET', '/q/' + this.value);
            Http.onload = function() {
                if(Http.status === 200) {
                    let results = JSON.parse(Http.responseText);
                    results.forEach(function(result) {
                        console.log(result.fields.name);
                    });
                } else {
                    console.log('Internal error: ' + Http.responseText);
                }
            }
            Http.send();
        }
    }
    document.getElementById('search').addEventListener('submit', function(e) {
        e.preventDefault();
        document.getElementById('filter').value = search.value;
        form.submit();
    }, true);
}



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