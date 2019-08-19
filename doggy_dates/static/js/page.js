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
const alertArea = $('#alertArea');
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
               alertArea.html(response);
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
    $('#registerForm')[0].reset();
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
           self.siblings().removeClass('hidden');
           alertArea.html(response);
           deleteAlertHandler();
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
 $('#email').keyup(function(){
     const emailStatus = $('#email_status');
     $.ajax({
         url: '/email',
         method: 'POST',
         data: $('#registerForm').serialize()
     })
         .done(function(response){
             if (!emailStatus.hasClass(response.code)) {
                 emailStatus.removeClass().addClass(response.code)
             }
             emailStatus.html(response.message);
             if (response.code === 'text-danger') {
                 $('#registerSubmit').addClass('disabled')
             } else {
                 $('#registerSubmit').removeClass('disabled')
             }
         });
     return false;
 });
 $('#confirm_pw').keyup(function(){
     const password = $('#password').val();
     if (password !== $('#confirm_pw').val()) {
         $('#registerSubmit').addClass('disabled');
         $('#pw_status').addClass('text-danger').html("Passwords don't match")
     } else {
         $('#registerSubmit').removeClass('disabled');
         $('#pw_status').html('')
     }
 });
 const nameRegEx = new RegExp('^[-a-zA-Z]+$');
 const registerErrors = [
     "Password must be at least 8 characters",
     "name must be at least two characters",
     "name can only contain '-' and alphabetic characters",
     "Passwords must match"
 ];
 $('#registerForm').submit(function(){
     if ($('#registerSubmit').hasClass('disabled')){
         return false;
     }
     alertArea.html('');
     const firstName = $('#firstName').val();
     const lastName = $('#lastName').val();
     const password = $('#password').val();
     let errorList = [];
     if (password.length < 8) {
         errorList.push(registerErrors[0])
     }
     if (firstName.length < 2) {
         errorList.push('First ' + registerErrors[1])
     }
     if (firstName.length >= 2 && !nameRegEx.test(firstName)) {
         errorList.push('First ' + registerErrors[2])
     }
     if (lastName.length >= 2 && !nameRegEx.test(lastName)) {
         errorList.push('Last ' + registerErrors[2])
     }
     if (lastName.length < 2) {
         errorList.push('Last ' + registerErrors[1])
     }
     if (password !== $('#confirm_pw').val()) {
         errorList.push(registerErrors[3])
     }
     errorList.forEach(function(error){
         alertArea.append(`<li class="alert alert-error" role="alert">${error}<i class="fas fa-times float-right icon-alert"></i></li>`)
     });
     deleteAlertHandler();
     if (errorList.length === 0){
         $.ajax({
             url: '/register',
             method: 'POST',
             data: $(this).serialize()
         })
             .done(function(){
                 window.location.href = '/'
             })
     }
     return false;
 });