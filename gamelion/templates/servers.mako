<%def name="game_checkbox(name, game_name)">
    <span class="checkbox_group">
        %if name in request.params:
            <input type="checkbox" name=${name} value="" checked />
        %else:
            <input type="checkbox" name=${name} value="" />
        %endif
        <span class="small_text">${game_name}</span>
    </span>
</%def>

<html>
<title>Server List</title>
<link rel="stylesheet" type="text/css" href="/style.css" />
<body>
<form name="search_box" method="GET">
<p>
    Search: 
    <input class="text_input" type="text" name="search" />
    <input class="button" type="submit" value="Go"/>
    </br>
    ${game_checkbox("css", "Counter-Strike: Source")}
    ${game_checkbox("tf2", "Team Fortress 2")}
    ${game_checkbox("cs1.6", "Counter-Strike 1.6")}
</p>
</form>
<p>${c.paginator.pager('~5~')}</p>
<table id="servers">
<tr>
    <th>Name</th>
    <th>Game</th>
    <th>IP Address</th>
</tr>
<% isAlt = False %>
% for server in c.paginator:
    % if isAlt:
    <tr class="alt1">
    % else:
    <tr class="alt2">
    % endif
        <td class="name">${server.name}</td>
        <td>${server.app_name}</td>
        <td>${server.address}:${server.port}</td>
    </tr>
    <% isAlt = not isAlt %>
% endfor
</table>
</body>
</html>

