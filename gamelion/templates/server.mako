<%inherit file="/base.mako" />
<%def name="title()">Server</%def>
<%def name="scripts()">
    ${parent.scripts()}
    <script type="text/javascript" src="/server.js"></script>
</%def>

<div id="refresh"></div>
<p>Players: <span id="players">Unknown</span></p>
