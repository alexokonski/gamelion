<%inherit file="/base.mako" />
<%def name="title()">Servers</%def>

<%def name="scripts()">
    ${parent.scripts()}
    <script type="text/javascript" src="/servers.js"></script>
</%def>

<%def name="game_checkbox(app_id, num, game_name)">
    <span class="checkbox_group">
        <input type="checkbox" name="game-${num}" value=${app_id} />
        <label class="small_text">${game_name}</label>
    </span>
</%def>

<h1><a href="/">Gamelion</a></h1>

<%def name="pager()">
    <p>${c.paginator.pager('~5~')}</p>
</%def>

<form id="search_form" name="search_form" method="GET">
<p>
    Search: 
    <input class="text_input" type="text" name="search" />
    <input class="button" type="submit" value="Go"/>
    <br/>
    <div class="primary_checkboxes">
    <% i = 0 %>
    % for id in c.primary_app_ids:
        ${game_checkbox(id, i, c.primary_app_ids[id])}  
        <% i += 1 %>
    % endfor
    </div>
    <div class="secondary_checkboxes">
    <% i = 0 %>
    % for id in c.secondary_app_ids:
        ${game_checkbox(id, i, c.secondary_app_ids[id])}  
        <% i += 1 %>
    % endfor   
    </div>
</form>
<a id="form_toggle" href="#"></a>
</p>

${pager()}
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
        <td class="name"><a href="${url(controller='server', address=server.address + ':' + str(server.port))}">${server.name}</a></td>
        <td>${server.app_name}</td>
        <td>${server.address}:${server.port}</td>
    </tr>
    <% isAlt = not isAlt %>
% endfor
</table>
${pager()}

