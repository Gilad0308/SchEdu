$(document).ready(function() {
    $("#btnFetch").click(function() {
    
    // add spinner to button
    $(this).html(
        `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Working on it...`
    );
    //Form sumbition
    document.getElementById("create_schedule").submit();

    });
});