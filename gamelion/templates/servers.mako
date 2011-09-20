<%! import datetime %>
<%! from gamelion.lib.queryserver import get_time_string %>
<%inherit file="/base.mako" />
<%def name="title()">Servers</%def>

<%def name="scripts()">
    ${parent.scripts()}
    <script type="text/javascript" src="/servers.js"></script>
</%def>

<%def name="checkbox(box)">
    <span class="checkbox_group">
        <label class="small_text">
        <input type="checkbox" name="${box.name}" value=${box.value} />
        ${box.label}
        </label>
    </span>
    <br/>
</%def>

<%def name="checkbox_group(group)">
    <div class="checkboxes">
    <fieldset>
    <legend>${group.label}</legend>
    <span class="primary_checkboxes">
    % for i in xrange(group.number_initially_visible):
        ${checkbox(group.checkboxes[i])}
    % endfor
    </span>

    <span class="secondary_checkboxes">
    % for i in xrange(group.number_initially_visible, len(group.checkboxes)):
        ${checkbox(group.checkboxes[i])}
    % endfor
    </span>

    <a class="form_toggle" href="#"></a>
    </fieldset>
    </div>
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
    % for group in c.checkbox_groups:
        ${checkbox_group(group)}
    % endfor
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

