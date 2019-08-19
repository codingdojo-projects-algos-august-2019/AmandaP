$(document).ready(function(){
    $('#register_section').hide();
    if ($('#attendingEvents').children().length === 0) {
        $('#noEventsAttending').html(`<td colspan="5">You have no upcoming events</td>`)
    };
    if ($('#hostingEvents').children().length === 0) {
        $('#noEventsHosting').html(`<td colspan="5">You are hosting no events</td>`)
    };
    leaveHandler();
    joinHandler();
    deleteMsgHandler();
    deleteAlertHandler();
    $.ajax({
        url: '/get_dogs',
        method: 'POST'
    })
        .done(function(response){
            $('#navBar').html(response)
        })
});
// handlers
function leaveHandler() {
$('.leaveLink').click(function(){
    const self = $(this);
    $.ajax({
        url: self.attr('href') + self.attr('data-action'),
        method: 'POST'
    })
       .done(function(response) {
           if (self.attr('data-page') === 'dashboard'){
               self.parent().parent().hide();
                if ($('#attendingEvents').children().length === 1) {
                    $('#noEventsAttending').html(`<td colspan="5">You have no upcoming events</td>`)
                }
           }
               $('#alertArea').html(response);
               deleteAlertHandler();
               self.attr('data-action', '/join').text('Join');
               $.ajax({
                   url: '/events/update',
                   method: 'GET'
               })
                   .done(function(response){
                       $('#eventTable').html(response);
                       joinHandler();
                       leaveHandler();
                   })
    });
   return false
});
}
function joinHandler() {
    $('.joinLink').click(function () {
        const self = $(this);
        $.ajax({
            url: self.attr('href') + self.attr('data-action'),
            method: 'POST'
        })
            .done(function (response) {
               $('#alertArea').html(response);
               deleteAlertHandler();
               self.attr('data-action', '/leave').text('Leave');
               $.ajax({
                   url: '/events/update',
                   method: 'GET'
               })
                   .done(function(response){
                       $('#eventTable').html(response);
                       joinHandler();
                       leaveHandler();
                   })
            });
        return false
    });
}
function deleteMsgHandler() {
    $('.icon-message').click(function(){
    const parent = $(this).parent();
   $.ajax({
        url: `/messages/${$(this).attr('data-msg-id')}/delete`,
        method: 'GET',
    })
       .done(function (response) {
           parent.hide();
           deleteAlertHandler();
            if ($('#messageArea').children().length === 1) {
                $('#messageArea').html(`<li class="list-group-item">No event messages</li>`)
            }
       });
   return false
});
}
function deleteAlertHandler() {
$('.icon-alert').click(function(){
   $(this).parent().css('display', 'none');
});
}
// login function switch between login and register
$('#change_section_register, #change_section_login').click(function() {
    $('#login_section').toggle();
    $('#register_section').toggle();
});
$('#cancelBtn').click(function(){
    window.location.href="/dashboard";
});
$('#cancelEditBtn').click(function(){
    window.location.href=`/${$(this).attr('data-page')}/${$(this).attr('datasrc')}`;
});
$('.actionBtns').click(function(){
    const self = $(this);
    if (self.hasClass('disabled')) {
        return;
    }
       $.ajax({
        url: `/events/${$(this).attr('datasrc')}/${$(this).attr('data-action')}`,
        method: 'POST',
    })
       .done(function(response) {
           self.addClass('hidden');
           self.siblings().removeClass('hidden')
           $('#alertArea').html(response);
           deleteAlertHandler();
    });
    return false
});
$('#eventForm').submit(function(){
    $.ajax({
        url: '/events/create',
        method: 'POST',
        data: $('#eventForm').serialize()
    })
                .done(function(response){
                   $('#alertArea').html(response);
                   deleteAlertHandler();
                   $('#eventForm')[0].reset();
                });
    return false
});
$('.deleteLink').click(function(){
    const self = $(this);
    $.ajax({
        url: self.href,
        method: 'GET'
    })
        .done(function(){
            window.location.href = `${self.attr('data-return')}`
        });
    return false
});
 $('#searchBar').keyup(function(){
        $.ajax({
        url: `/events/update`,
            data: $('#searchForm').serialize(),
        method: 'POST',
    })
        .done(function(response){
           $('#eventTable').html(response);
           joinHandler();
           leaveHandler();
        });
        return false;
    });