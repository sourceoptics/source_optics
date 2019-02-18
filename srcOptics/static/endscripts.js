document.getElementById('repos').onchange = function() {
    const Http = new XMLHttpRequest();
    Http.open('GET', '/repo/?id=' + event.target.value);
    Http.send();
    Http.onreadystatechange=(e)=>{
      document.getElementById('commits').innerHTML = Http.responseText;
    }
};