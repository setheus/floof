# encoding: utf8
import logging

from pyramid import httpexceptions
from pyramid.renderers import render_to_response
from pyramid.view import view_config

from floof.app import NoCookiesError
from floof.lib.authz import UPGRADABLE_PRINCIPALS
from floof.lib.authz import outstanding_principals


log = logging.getLogger(__name__)


def error_view(exc, request, default_message, status=None,
               outstanding_principals=None, renderer='error.mako'):

    # Preserve a previously set status code unless specifically overridden
    if request.response.status != '200 OK':
        status = status or request.response.status
    else:
        status = status or getattr(exc, 'status', None) or 500

    request.response.status = status

    if len(exc.args) and exc.args[0]:
        message = exc.args[0]
    else:
        message = default_message

    data = {
        'http_status': status,
        'message': message,
        'outstanding_principals': outstanding_principals,
    }

    if not renderer:
        return data
    elif request.is_xhr:
        return render_to_response('json', data, request)
    return render_to_response(renderer, data, request)


@view_config(context=httpexceptions.HTTPBadRequest)
def error400(exc, request):
    default_msg = u"I'm afraid I can't let you do that"
    return error_view(exc, request, default_msg)


@view_config(context=httpexceptions.HTTPForbidden)
def error403(exc, request):
    outstanding = []

    if request.user.can(request.permission):
        all_outstanding = outstanding_principals(
            request.permission, request.context, request)
        for altset in all_outstanding:
            if all(p for p in altset if p.startswith(UPGRADABLE_PRINCIPALS)):
                outstanding.append(tuple(altset))

    outstanding = list(set(outstanding))  # Unique-ify
    outstanding.sort(key=len)

    default_msg = u"I'm afraid I can't let you do that"
    return error_view(exc, request, default_msg,
                      outstanding_principals=outstanding)


@view_config(context=httpexceptions.HTTPNotFound)
def error404(exc, request):
    # XXX this can probably be improved
    default_msg = u"No such number // no such zone  ♪"
    return error_view(exc, request, default_msg)


@view_config(context=NoCookiesError)
def no_cookies_error(exc, request):
    msg = (u"It appears cookies may be disabled in your browser.  "
           "Unfortunately, this site requires cookies in order for you to log "
           "in and to perform any actions such as submitting art or changing "
           "your personal settings.  To enable cookies, please refer to your "
           "browser's instructions on privacy or security settings.")
    return error_view(exc, request, msg, status=400)


def error500(exc, request):
    """Catch-all error handler; imperatively added in floof.app.main."""
    default_msg = u"everything is fine.  nothing is ruined._"
    return error_view(exc, request, default_msg, status='500 Server On Fire')
