"use strict";

$(function() {
    if($(".secondary_checkboxes").find("input:checked").val() == undefined)
    {
        $(".secondary_checkboxes").hide();
        $("#form_toggle").text("More Games")
    }
    else
    {
        $("#form_toggle").text("Less Games")
    }
    
    $("#form_toggle").click(function() {
        $(".secondary_checkboxes").slideToggle("fast", function() {
            if($(".secondary_checkboxes").is(":visible"))
            {
                $("#form_toggle").text("Less Games");
            }
            else
            {
                $("#form_toggle").text("More Games");
            }
        });
    });
});
