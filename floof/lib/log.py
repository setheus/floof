from pylons import request, response, session, tmpl_context as c, url

from floof import model
from floof.model import Log, meta

from datetime import datetime
import logging
from logging import *

"""
Library for a very simple logging filter and handler for DB insertion of
log records.

To use, issue statements like the following in a controller:

    log.info('A description of the log')
or
    log.log(ADMIN, 'An admin action log')
or
    log.log(ADMIN, 'This admin action log will be publically viewable', extra={'visibility':'public'})

ADMIN is a constant defined in this module.  You'll need something like:
    from floof.lib.log import ADMIN

If the request triggering the log required permissions to complete, the
filter will attempt to log which privileges held by the user were
invoked by the request.  Privileges checked by a `@user_must('priv')
decorator in a controller are automatically logged.  To inform the logger
if any other privileges were excercised, set the keyword flag `log` to
True when you use c.user.can.  e.g.:
    c.user.can('priv', log=True)

Note that the current behaviour should a log record attempt to make
public an action that did not require a privilege prefixed with 'admin.'
is to raise an exception.

"""

# Between INFO (20) and WARNING (30).
ADMIN = 25
logging.addLevelName(ADMIN, 'ADMIN')

class FloofFilter(Filter):
    """
    A filter which injects contextual information into the log.

    """
    def filter(self, record):
        record.user = None
        record.username = None
        record.privileges = []
        if not hasattr(record, 'visibility'):
            record.visibility = 'admin'
        has_admin_privs = False
        if c.user:
            record.user = c.user
            record.username = c.user.name
            record.privileges = c.user.logged_privs()
            for priv in c.user.logged_privs():
                if priv.name.startswith('admin.'):
                    has_admin_privs = True
        if record.visibility == 'public' and not has_admin_privs:
            raise RuntimeError('Attempted to log a non-admin action publically.')
        record.url = url.current()
        # XXX: Fix this to account for proxied requests (e.g. via nginx).
        record.ipaddr = request.remote_addr
        return True

class FloofDBHandler(Handler):
    def __init__(self, level=NOTSET):
        Handler.__init__(self, level)
        self.addFilter(FloofFilter())

    def emit(self, record):
        entry = Log(
                visibility=record.visibility,
                timestamp=datetime.fromtimestamp(record.created),
                logger=record.name,
                level=record.levelno,
                url=record.url,
                user=record.user,
                privileges=record.privileges,
                ipaddr=record.ipaddr,
                target_user=None,
                message=unicode(record.getMessage()),
                reason=None,
                )
        meta.Session.add(entry)
        meta.Session.commit()

class FloofFileHandler(FileHandler):
    """Simply adds a FloofFilter to a FileHandler.  Alas, this can't be done
    via the paster config file.
    """
    def __init__(self, *args):
        FileHandler.__init__(self, *args)
        self.addFilter(FloofFilter())
