$(document).ready(function(){
    $.ajax({
        url: 'https://dog.ceo/api/breeds/image/random',
        method: 'GET'
    })
        .done(function(response){
            $('#puppyImg').append(`<img src='${response.message}' alt="random_dog_pic">`)
        });
});