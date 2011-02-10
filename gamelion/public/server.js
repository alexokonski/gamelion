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
        $("#password").text(data.password_required ? "Yes" : "No");
        $("#bots").text(data.number_of_bots);
        $("#secure").text(data.is_secure ? "Yes" : "No");
        $("#version").text(data.version);
        $("#os").text(data.os);

        obj = $("#players_table").find("tbody").empty();

        players = data.players
        for(i=0; i<players.length; i++)
        {
            var time = players[i].time_connected;
            var hours = Math.floor((time / 3600));
            var minutes = Math.floor((time % 3600) / 60);
            var seconds = Math.floor((time % 3600) % 60);

            obj = obj.append($("<tr>")
                        .append($("<td>")
                            .text(players[i].name)
                        ).append($("<td>")
                            .text(players[i].kills)
                        ).append($("<td>")
                            .text(hours.toPrecision(2) + 
                                    ":" + 
                                    minutes.toPrecision(2) + 
                                    ":" + 
                                    seconds.toPrecision(2))
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
        timeout: 7000,
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
