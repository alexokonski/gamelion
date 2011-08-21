"use strict";

$(function() {
    var checkDiv = ".secondary_checkboxes";

    $(checkDiv).hide();
    $(checkDiv).each(function() {
        if($(this).find("input:checked").val() != undefined ) {
            $(this).show();
            $(this).next(".form_toggle").text("Less");
        } else {
            $(this).hide();
            $(this).next(".form_toggle").text("More");
        }
    });
    
    $(".form_toggle").click(function() {
        var checkboxes = $(this).parent("fieldset")
                                .children(".secondary_checkboxes");
        checkboxes.slideToggle("fast");

        if(checkboxes.is(":visible")) {
            $(this).text("More");
        } else {
            $(this).text("Less");
        }
    });
});
