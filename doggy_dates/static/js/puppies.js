$(document).ready(function(){
    $('img').click(function(){
    $.ajax({
        url: 'https://dog.ceo/api/breeds/image/random',
        method: 'GET'
    })
        .done(function(response){
            $('img').attr('src', response.message);
        });
    });
    return false
});