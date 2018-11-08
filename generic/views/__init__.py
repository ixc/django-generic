from django import http
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout as auth_logout
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render_to_response, redirect

try:
    # Prevent deprecation warnings on Django >= 1.4
    from django.conf.urls import url
except ImportError:
    # For compatibility with Django <= 1.3
    from django.conf.urls.defaults import url


def server_error(request, template_name='500.html'):
    """
    Custom HTTP 500 handler which includes MEDIA_URL, etc.
    Must be careful not to include anything in any way fragile into
    the context.
    """
    # don't risk running context processors
    context = dict(settings.TEMPLATE_CONSTANTS)
    context['MEDIA_URL'] = settings.MEDIA_URL
    context['STATIC_URL'] = settings.STATIC_URL
    context['request'] = request
    return render_to_response(template_name, context)

def logout(request):
    """
    Log someone out and return to the homepage
    """
    auth_logout(request)
    messages.success(request, 'You are now logged out')
    return redirect('/')

def relative_view_on_site(request, content_type_id, object_id):
    """
    Redirect to an object's page based on a content-type ID and an object ID,
    always using a relative path, thus not requiring the Sites framework to be
    set up. To use, add the following entry in the URLconf _above_ the admin URL
    declaration (or use `relative_view_on_site_urls`):

    url(r'^admin/r/(?P<content_type_id>\d+)/(?P<object_id>.+)/$',
        'generic.views.relative_view_on_site'),

    The code is almost entirely copied from the shortcut() view in
    django.contrib.contenttypes.views
    """
    try:
        content_type = ContentType.objects.get(pk=content_type_id)
        if not content_type.model_class():
            raise http.Http404("Content type %s object has no associated model" % content_type_id)
        obj = content_type.get_object_for_this_type(pk=object_id)
    except (ObjectDoesNotExist, ValueError):
        raise http.Http404("Content type %s object %s doesn't exist" % (content_type_id, object_id))
    try:
        return http.HttpResponseRedirect(obj.get_absolute_url())
    except AttributeError:
        raise http.Http404("%s objects don't have get_absolute_url() methods" % content_type.name)

relative_view_on_site_urls = url(
    r'^admin/r/(?P<content_type_id>\d+)/(?P<object_id>.+)/$',
    relative_view_on_site,
)
