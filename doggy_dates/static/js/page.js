$(document).ready(function(){
    // if there is a register section
    $('#register_section').hide();
    /* $('.weatherAPI').each( function() {
        const self = $(this);
            const zipcode = $(this).attr('datasrc');
            const time = $(this).attr('data-time');
            console.log(time)
            $.ajax({
                url: `http://weather.api.here.com/weather/1.0/report.json?app_id=hTbK4O9DbrxVabKcFg9C&app_code=xd7WMhnk_GKoFfLViHyntA&product=forecast_hourly&zipcode=${zipcode}&hourlydate=${time}`,
                method: 'GET',
            })
                .done(function (response) {
                    self.append(
                        `<img src="${response.observations.location[0].observation[0].iconLink}" height="35" width="35">`)
                })
        })
     */
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
$('#cancelBtn').click(function(){
    window.location.href="/dashboard";
});
