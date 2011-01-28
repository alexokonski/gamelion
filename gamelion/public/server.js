"use strict";

$(function() {
    function display_error() {
        $("#refresh a")
            .empty()
            .text('Refresh Failed... Try again')
            .show();
    }

    $.ajaxSetup({
        cache: false,
        dataType: 'json',
        error: function (request, textStatus, errorThrown) {
            display_error();
        },
        success: function (data, textStatus, request) {
            $("#refresh a").text('Refresh')
            $("#players").text(data.players + '/' + data.max_players);    
        },
        timeout: 5000,
        type: 'GET',
        url: '?json=1'
    });

    function refresh() {
        $("#refresh a").text("Refreshing...")
        $.ajax({
            data: { 'refresh' : 1 }
        });
    }

    $("#refresh")
        .append("<a href='#'>Refresh</a>")
        .click(function(e) {
            e.preventDefault();
            refresh();
        });

    refresh();
});
