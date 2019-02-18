document.getElementById('repos').addEventListener('change', (event) => {
    const Http = new XMLHttpRequest();
    Http.open('GET', '/?repo=' + event.target.value);
    Http.send();
    Http.onreadystatechange=(e)=>{
      console.log(Http.responseText);
        document.body.innerHTML = Http.responseText;
    }
});