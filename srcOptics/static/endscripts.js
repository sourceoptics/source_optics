document.getElementById('repos').addEventListener('change', (event) => {
    const Http = new XMLHttpRequest();
    Http.open('GET', '');
    Http.send(event.target.value);
    Http.onreadystatechange=(e)=>{
        //console.log(Http.responseText)
    }
});