"use strict";

$(function() {
    var checkDiv = ".secondary_game_checkboxes"
    if($(checkDiv).find("input:checked").val() == undefined) {
        $(".secondary_game_checkboxes").hide();
        $("#form_toggle").text("More Games")
    } else {
        $("#form_toggle").text("Less Games")
    }
    
    $("#form_toggle").click(function() {
        $(checkDiv).slideToggle("fast", function() {
            if($(checkDiv).is(":visible")) {
                $("#form_toggle").text("Less Games");
            } else {
                $("#form_toggle").text("More Games");
            }
        });
    });
});
