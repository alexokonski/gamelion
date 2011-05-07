"use strict";

$(function() {
    function display_error() {
        $("#refresh a")
            .empty()
            .text('Refresh Failed... Try again')
            .show();
    }

    function process_success(data) {
        if (data.success === false) return;

        $("#refresh a").text('Refresh')
        $("#players").text(data.number_of_players + '/' + data.max_players);
        $("#map").text(data.map);
        $("#password").text(data.password_required);
        $("#bots").text(data.number_of_bots);
        $("#secure").text(data.is_secure);
        $("#version").text(data.version);
        $("#os").text(data.os);

        var obj = $("#players_table").find("tbody").empty();

        var players = data.players
        for(var i=0; i<players.length; i++)
        {
            obj = obj.append($("<tr>")
                        .append($("<td>")
                            .text(players[i].name)
                        ).append($("<td>")
                            .text(players[i].kills)
                        ).append($("<td>")
                            .text(players[i].time_connected)
                        )
                     );
        }
    }

    $.ajaxSetup({
        cache: false,
        dataType: 'json',
        error: function (request, textStatus, errorThrown) {
            display_error();
        },
        success: function (data, textStatus, request) {
            process_success(data);
        },
        timeout: 20000,
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
