$(document).ready(function(){
    $('#register_section').hide();
    if ($('#attendingEvents').children().length === 0) {
        $('#noEventsAttending').html(`<td colspan="5">You have no upcoming events</td>`)
    };
    if ($('#hostingEvents').children().length === 0) {
        $('#noEventsHosting').html(`<td colspan="5">You are hosting no events</td>`)
    };
});

// login function switch between login and register
$('#change_section_register, #change_section_login').click(function() {
    $('#login_section').toggle();
    $('#register_section').toggle();
});
// to click out of alert icons...
$('.icon-alert').click(function(){
   $(this).parent().css('display', 'none');
});
// to delete items and have them disappear
$('.icon-message').click(function(){
    const parent = $(this).parent();
   $.ajax({
        url: `messages/${$(this).attr('data-message-id')}/delete`,
        method: 'GET',
    })
       .done(function (response) {
           parent.css('display', 'none');
       });
   return false
});
$('#cancelBtn').click(function(){
    window.location.href="/dashboard";
});
$('#leaveLink').click(function(){
   console.log($('#attendingEvents').children().length);
    const parent = $(this).parent();
    $.ajax({
        url: $(this).attr('href'),
        method: 'GET'
    })
       .done(function(response) {
           parent.parent().hide();
    if ($('#attendingEvents').children().length === 1) {
        $('#noEventsAttending').html(`<td colspan="5">You have no upcoming events</td>`)
    }
    });
    return false
});
$('#joinLink').click(function(){
    $.ajax({
        url: $(this).attr('href'),
        method: 'GET'
    })
       .done(function() {
        window.location.href="/events";
    });
    return false
});
$('#leaveLinkEventsPage').click(function(){
    $.ajax({
        url: $(this).attr('href'),
        method: 'GET'
    })
       .done(function() {
        window.location.href="/events";
    });
    return false
});

$('.actionBtns').click(function(){
    const self = $(this);
    if (self.hasClass('disabled')) {
        return;
    }
       $.ajax({
        url: `/events/${$(this).attr('datasrc')}/${$(this).attr('data-action')}`,
        method: 'GET',
    })
       .done(function(response) {
           self.addClass('hidden');
           self.siblings().removeClass('hidden')
    });
    return false
});

