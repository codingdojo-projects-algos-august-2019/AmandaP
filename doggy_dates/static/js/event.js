$(document).ready(function(){

});
 $('#searchBar').keyup(function(){
        $.ajax({
        url: `/events/search`,
            data: $('#searchForm').serialize(),
        method: 'POST',
    })
        .done(function(response){
           $('#eventTable').html(response)
        });
        return false;
    });