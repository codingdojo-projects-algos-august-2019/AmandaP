$(document).ready(function(){
    // if there is a register section
    $('#register_section').hide();
});

// login function switch between login and register
$('#change_section_register, #change_section_login').click(function() {
    $('#login_section').toggle();
    $('#register_section').toggle();
});
// if you have a like functionality or a follow/unfollow
$('#like_heart').click(function() {
   $.ajax({
        url: `${$('#like_heart').attr('href')}`,
        method: 'GET',
    })
        .done(function (response) {
           $('#like_heart').attr('class', response.class).attr('href', response.href);
        });
    return false
});
// to click out of alert icons...
$('.icon-alert').click(function(){
   $(this).parent().css('display', 'none');
});
// to delete items and have them disappear
$('.icon-comment').click(function(){
    const parent = $(this).parent();
   $.ajax({
        url: `comments/${$(this).attr('data-comment-id')}/delete`,
        method: 'GET',
    })
       .done(function (response) {
           parent.css('display', 'none');
       });
   return false
});

