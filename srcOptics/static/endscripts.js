/**
 * @file endscripts.js
 * Provides additional tweaks to front-end components
 *
 * These additional scripts are intended to be run at the end
 * of the document after all elements have been rendered
 */

'use strict';

/** Set default start date back one week from current
 * date on #range .start input element
 */

const defaultRange = 7;

var form = document.getElementById('range');
let start = form.querySelector('.start');
if(!start.value) {
    let now = new Date();
    now.setDate(now.getDate() - defaultRange);
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

/** 
 * Used to submit search query along with existing query strings
 * @param obj Object / node to pull value from
 * @param e Event
 */
var submitQuery = function(obj, e) {
    e.preventDefault();
    document.getElementById('filter').value = obj.value;
    form.submit();
};

// Search elements
var search = document.querySelector('#search input');
var searchForm = document.getElementById('search');
var results = document.querySelector('.results');

if(search) {
    // Replaces default submit in search box
    searchForm.addEventListener('submit', submitQuery.bind(null, search), true);

    /** 
     * Triggers live search using ajax and populates results
     */
    search.onkeyup = function() {
        
        // Check if search box is not empty
        if(this.value) {
            
            // Make a new ajax GET request
            let Http = new XMLHttpRequest();
            Http.open('GET', '/q/' + this.value);

            Http.onload = function() {
                if(Http.status === 200) { // if successful

                    // Parse request response into an array of JSON objects
                    let res = JSON.parse(Http.responseText);

                    // Initialize results to be empty, loop through and create elements
                    results.innerHTML = '';
                    res.forEach(function(e) {
                        results.innerHTML += `<li><span onclick="submitQuery({value:'${e.fields.name}'},event);">${e.fields.name}</span></li>`;
                    });

                    // Add result for searching a query manually
                    results.innerHTML += `<li><span onclick="searchForm.dispatchEvent(new Event('submit'));">Search for '${search.value}'</span></li>`;

                } else { // if fail, print response text to console
                    console.log('Internal error: ' + Http.responseText);
                }
            }
            Http.send();
        }
    }
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