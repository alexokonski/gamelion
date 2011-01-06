<html>
<title>Server List</title>
<link rel="stylesheet" type="text/css" href="/style.css" />

<form name="search_box" method="GET" />
Search: <input type="text" name="search" />
        <input type="submit" name="submit" value="Submit" />
</form>

<table id="servers">
<tr>
    <th>Name</th>
    <th>IP Address</th>
</tr>
<% isAlt = False %>
% for server in c.servers:
    % if isAlt:
    <tr class="alt1">
    % else:
    <tr class="alt2">
    % endif
        <td>${server.name}</td>
        <td>${server.address}:${server.port}</td>
    </tr>
    <% isAlt = not isAlt %>
% endfor
</table>
</html>

