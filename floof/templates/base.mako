<!DOCTYPE html>
<html>
<head>
    <title>${self.title()}</title>
</head>
<body>
    <div id="header">
        <div id="user">
            % if c.user:
                ${h.form(url(controller='account', action='logout'), class_='compact')}
                <p>
                    Logged in as ${c.user.display_name}.
                    <button type="submit">Log out</button>
                </p>
                ${h.end_form()}
            % else:
            <a href="${url(controller='account', action='login')}">Log in or register</a>
            % endif
        </div>
    </div>

    <% flash = h._flash.pop_messages() %>
    % if flash:
    <ul id="flash">
        % for message, extras in flash:
        <li>${message}</li>
        % endfor
    </ul>
    % endif

    <div id="content">
        ${next.body()}
    </div>
</body>
</html>

<%def name="title()">Untitled</%def>
