<%! import datetime %>
<%! from gamelion.lib.queryserver import get_time_string %>
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
    <br/>
</%def>

<%def name="options_checkbox(option_id, option_name)">
    <span class="checkbox_group">
        <input type="checkbox" name="server_option" value=${option_id} />
        <label class="small_text">${option_name}</label>
    </span>
    <br/>
</%def>

<h1><a href="/">Gamelion</a></h1>

<%def name="pager()">
    <p class="pager">${c.paginator.pager('~5~')}</p>
</%def>

<p>
<form id="search_form" name="search_form" method="GET">
    Search: 
    <input class="text_input" type="text" name="search" />
    <input class="button" type="submit" value="Go"/>
    <br/>
    <div class="game_checkboxes">
    <fieldset>
        <legend>Games</legend>
        <span class="primary_game_checkboxes">
        <% i = 0 %>
        % for app in c.app_ids[:c.NUM_PRIMARY_CHECK_BOXES]:
            ${game_checkbox(app.app_id, i, app.app_name)}  
            <% i += 1 %>
        % endfor
        </span>
        <div class="secondary_game_checkboxes">
        % for app in c.app_ids[c.NUM_PRIMARY_CHECK_BOXES:]:
            ${game_checkbox(app.app_id, i, app.app_name)}  
            <% i += 1 %>
        % endfor   
        </div>
        <a id="form_toggle" href="#"></a>
    </fieldset>
    </div>
    <div class="options_checkboxes">
    <fieldset>
        <legend>Server Options</legend>
    </fieldset>
    </div>
</form>
</p>

${pager()}

<table id="servers">
<tr>
    <th>Name</th>
    <th>Game</th>
    <th>Players</th>
    <th>Last Update</th>
    <th>IP Address</th>
</tr>
<% isAlt = False %>
<% now = datetime.datetime.now() %>
% for server in c.paginator:
    % if isAlt:
    <tr class="alt1">
    % else:
    <tr class="alt2">
    % endif
        <td class="name"><a href="${url(controller='server', address=server.address + ':' + str(server.port))}">${server.name}</a></td>
        <td>${server.app_name}</td>
        <td>${server.number_of_players}/${server.max_players}</td>
        <% delta = now - server.timestamp %>
        <% seconds = delta.days * 25 * 3600 + delta.seconds %>
        <td>${get_time_string(seconds=seconds, significant_only=True)}</td>
        <td>${server.address}:${server.port}</td>
    </tr>
    <% isAlt = not isAlt %>
% endfor
</table>
${pager()}

