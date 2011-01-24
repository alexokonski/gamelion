<%def name="game_checkbox(app_id, num, game_name)">
    <span class="checkbox_group">
        <input type="checkbox" name="game-${num}" value=${app_id} />
        <label class="small_text">${game_name}</label>
    </span>
</%def>

<html>
<title>Server List</title>
<link rel="stylesheet" type="text/css" href="/style.css" />
<body>
<form name="search_form" method="GET">
<p>
    Search: 
    <input class="text_input" type="text" name="search" />
    <input class="button" type="submit" value="Go"/>
    </br>
    <% i = 0 %>
    % for id in c.app_ids:
        ${game_checkbox(id, i, c.app_ids[id])}  
        <% i += 1 %>
    % endfor
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

