<%inherit file="/base.mako" />
<%def name="title()">${c.server.name}</%def>
<%def name="scripts()">
    ${parent.scripts()}
    <link rel="stylesheet" type="text/css" href="/server.css">
    <script type="text/javascript" src="/server.js"></script>
</%def>

<h1>${c.server.name}</h1>
<a href="/">Home</a>
<div id="refresh"></div>
<div id="settings_left">
<p>
IP: ${c.server.address}:${c.server.port}
</br>
Game: <span id="game">${c.server.app_name}</span>
</br>
Players: <span id="players">${c.server.number_of_players}/${c.server.max_players}</span>
</br>
Map: <span id="map">${c.server.map}</span>
</br>
Password: <span id="password">${c.server.password_required_str}</span>
</p>
</div>
<div id="settings_right">
<p>
Number of bots: <span id="bots">${c.server.number_of_bots}</span>
</br>
Secure: <span id="secure">${c.server.is_secure_str}</span>
</br>
Version: <span id="version">${c.server.version}</span>
</br>
OS: <span id="os">${c.server.operating_system_str}</span>
</br>
Hotness: <span id="hotness">${c.server.hotness_all_time}</span>
</p>
</div>

<table id="players_table">
<thead>
<tr>
    <th>Player</th>
    <th>Kills</th>
    <th>Time</th>
</tr>
</thead>
<tbody>
</tbody>
</table>
