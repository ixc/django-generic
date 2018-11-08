# originally based on http://djangosnippets.org/snippets/1720/

import base64
from functools import wraps

from django.conf import settings
from django.http import HttpResponse
from django.contrib.auth import authenticate

class HttpAuthMiddleware(object):
    """ Authenticate all requests """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return _http_auth_helper(request) or response


def default_auth_function(request, username, password):
    """ Return True upon successful authentication """
    user = authenticate(username=username, password=password)
    if user:
        request.user = user
        return True


def http_auth(func):
    """ Decorator for authenticating specific views """
    @wraps(func)
    def inner(request, *args, **kwargs):
        result = _http_auth_helper(request)
        if result is not None:
            return result
        return func(request, *args, **kwargs)
    return inner


def _http_auth_helper(request):
    if not getattr(settings, 'HTTP_AUTH_ENABLED', True):
        return None

    if not getattr(settings, 'HTTP_AUTH_ALWAYS', False):
        if request.user.is_authenticated():
            return None

    exemption_callable = getattr(
        settings, 'HTTP_AUTH_EXEMPTION_CALLABLE', None)
    if exemption_callable and exemption_callable(request):
        return None

    if 'HTTP_AUTHORIZATION' in request.META:
        auth = request.META['HTTP_AUTHORIZATION'].split()
        if len(auth) == 2:
            if auth[0].lower() == 'basic':
                username, password = base64.b64decode(auth[1]).decode().split(':')
                auth_function = getattr(
                    settings, 'HTTP_AUTH_FUNCTION', default_auth_function)
                if auth_function(request, username, password):
                    return None
            else:
                pass # only 'basic' currently supported

    response = HttpResponse(status=401)
    response['WWW-Authenticate'] = 'Basic realm="{}"'.format(
        getattr(settings, 'HTTP_AUTH_REALM', 'Restricted'))
    return response
