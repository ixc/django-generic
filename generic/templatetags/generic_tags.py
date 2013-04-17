import re

from django import forms
from django import template
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.db.models import get_model
from django.http import QueryDict
from django.template import Node
from django.template import TemplateSyntaxError
from django.template.defaultfilters import stringfilter, fix_ampersands
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe
from urlparse import urlparse

register = template.Library()

@register.inclusion_tag('_field.html')
def field(field, *args, **kwargs):
    return {
        'field': field,
        'show_label': kwargs.get('show_label', True),
        'show_star': kwargs.get('show_star', True),
        'label_override': kwargs.get('label_override', None),
        'checkbox': isinstance(field.field.widget, forms.CheckboxInput),
    }

@register.filter
def linkify(obj):
    """
    Renders a link to an object.
    """
    return mark_safe('<a href="%s">%s</a>' % (obj.get_absolute_url(), obj))

@register.filter
@stringfilter
def unbreakable(string):
    """
    Replaces spaces with non-breaking spaces
    and hyphens with non-breaking hyphens.
    """
    return mark_safe(
        string.strip().replace(' ', '&nbsp;').replace('-', '&#8209;'))

HTML_COMMENTS = re.compile(r'<!--.*?-->', re.DOTALL)
@register.filter
@stringfilter
def unescape(text):
    """
    Renders plain versions of HTML text - useful for supplying HTML into
    plain text contexts.
    """
    ENTITIES = {
        'amp': '&',
        'lt': '<',
        'gt': '>',
        'quot': '"',
        '#39': "'",
        'nbsp': ' ',
        'ndash': '-',
        'mdash': '--',
        'rsquo': "'",
        'rdquo': '"',
        'lsquo': "'",
        'ldquo': '"',
        'middot': '*',
        'hellip': '...',
        }
    text = HTML_COMMENTS.sub('', text)
    return re.sub(
        '&(%s);' % '|'.join(ENTITIES),
        lambda match: ENTITIES[match.group(1)], text)


LINE_BREAKS = re.compile(r'(<br\s*/*>)|(</p>)')
VERTICAL_WHITESPACE = re.compile(r'\s*\n\s*', re.DOTALL)
@register.filter
@stringfilter
def html_to_text(html):
    html = LINE_BREAKS.sub('\n', html)
    return VERTICAL_WHITESPACE.sub('\n\n', strip_tags(unescape(html))).strip()


def _get_admin_url(obj, view='change', admin_site_name='admin'):
    return reverse(
        '%(namespace)s:%(app)s_%(model)s_%(view)s' % {
            'namespace': admin_site_name,
            'app': obj._meta.app_label,
            'model': obj._meta.module_name,
            'view': view}, args=(obj.pk,))

@register.simple_tag
def admin_url(obj, view='change', admin_site_name='admin'):
    return _get_admin_url(obj, view, admin_site_name)

@register.simple_tag
def domain_only(full_url):
    """
    Return only the domain in a url.
    """
    parsed = urlparse(full_url)
    return parsed.netloc.lstrip("www.")


"""
split_list
==========
Split list into n sublists, eg. to enable the display of some results in
several columns in HTML. Based on http://djangosnippets.org/snippets/889/

    {% split_list people as my_list 3 %}
    {% for l in my_list %}
        <ul>
            {%for p in l %}
                <li>{{ p }}</li>
            {% endfor %}
        </ul>
    {% endfor %}

"""

@register.tag(name='split_list')
def split_list(parser, token):
    """Parse template tag: {% split_list list as new_list 2 %}"""
    bits = token.contents.split()
    if len(bits) != 5:
        raise TemplateSyntaxError, "split_list list as new_list 2"
    if bits[2] != 'as':
        raise TemplateSyntaxError, "second argument to the split_list tag must be 'as'"
    return SplitListNode(bits[1], bits[4], bits[3])

class SplitListNode(Node):
    def __init__(self, list, cols, new_list):
        self.list, self.cols, self.new_list = list, cols, new_list

    def split_seq(self, list, cols=2):
        start = 0
        for i in xrange(cols):
            stop = start + len(list[i::cols])
            yield list[start:stop]
            start = stop

    def render(self, context):
        context[self.new_list] = self.split_seq(context.get(self.list, []), int(self.cols))
        return ''


"""
captureas
=========
Renders the contents of a block, and stores the rendered result in a new variable.
Taken from http://www.djangosnippets.org/snippets/545/.

    {% captureas person_name %}{% complex_logic %}{% endcaptureas %}
    {% include "person.html" with name=person_name %}

Django's {% filter %} tag covers many of the same use cases.

"""
@register.tag(name='captureas')
def do_capture_as(parser, token):
    try:
        tag_name, args = token.contents.split(None, 1)
    except ValueError:
        raise template.TemplateSyntaxError("'captureas' node requires a variable name.")
    nodelist = parser.parse(('endcaptureas',))
    parser.delete_first_token()
    return CaptureasNode(nodelist, args)

class CaptureasNode(template.Node):
    def __init__(self, nodelist, varname):
        self.nodelist = nodelist
        self.varname = varname

    def render(self, context):
        output = self.nodelist.render(context)
        context[self.varname] = output
        return ''

"""
update_GET allows you to substitute parameters into the current request's
GET parameters. This is useful for updating search filters without losing
the current set.

{% load update_GET %}

<a href="?{% update_GET attr1 += value1 attr2 -= value2 attr3 = value3 %}">foo</a>
This adds value1 to (the list of values in) attr1,
removes value2 from (the list of values in) attr2,
sets attr3 to value3.

And returns a urlencoded GET string.

Allowed values are:
    strings, in quotes
    vars that resolve to strings
    lists of strings
    None (without quotes)

If a attribute is set to None or an empty list, the GET parameter is removed.
If an attribute's value is an empty string, or [""] or None, the value remains, but has a "" value.
If you try to =- a value from a list that doesn't contain that value, nothing happens.
If you try to =- a value from a list where the value appears more than once, only the first value is removed.
"""

@register.tag(name='update_GET')
def do_update_GET(parser, token):
    try:
        args = token.split_contents()[1:]
        triples = list(_chunks(args, 3))
        if triples and len(triples[-1]) != 3:
            raise template.TemplateSyntaxError, "%r tag requires arguments in groups of three (op, attr, value)." % token.contents.split()[0]
        ops = set([t[1] for t in triples])
        if not ops <= set(['+=', '-=', '=']):
            raise template.TemplateSyntaxError, "The only allowed operators are '+=', '-=' and '='. You have used %s" % ", ".join(ops)

    except ValueError:
        return UpdateGetNode()

    return UpdateGetNode(triples)

def _chunks(l, n):
    """ Yield successive n-sized chunks from l.
    """
    for i in xrange(0, len(l), n):
        yield l[i:i+n]


class UpdateGetNode(template.Node):
    def __init__(self, triples=[]):
        self.triples = [(template.Variable(attr), op, template.Variable(val)) for attr, op, val in triples]

    def render(self, context):
        try:
            GET = context.get('request').GET.copy()
        except AttributeError:
            GET = QueryDict("", mutable=True)

        for attr, op, val in self.triples:
            actual_attr = attr.resolve(context)

            try:
                actual_val = val.resolve(context)
            except:
                if val.var == "None":
                    actual_val = None
                else:
                    actual_val = val.var

            if actual_attr:
                if op == "=":
                    if actual_val is None or actual_val == []:
                        if GET.has_key(actual_attr):
                            del GET[actual_attr]
                    elif hasattr(actual_val, '__iter__'):
                        GET.setlist(actual_attr, actual_val)
                    else:
                        GET[actual_attr] = unicode(actual_val)
                elif op == "+=":
                    if actual_val is None or actual_val == []:
                        if GET.has_key(actual_attr):
                            del GET[actual_attr]
                    elif hasattr(actual_val, '__iter__'):
                        GET.setlist(actual_attr, GET.getlist(actual_attr) + list(actual_val))
                    else:
                        GET.appendlist(actual_attr, unicode(actual_val))
                elif op == "-=":
                    li = GET.getlist(actual_attr)
                    if hasattr(actual_val, '__iter__'):
                        for v in list(actual_val):
                            if v in li:
                                li.remove(v)
                        GET.setlist(actual_attr, li)
                    else:
                        actual_val = unicode(actual_val)
                        if actual_val in li:
                            li.remove(actual_val)
                        GET.setlist(actual_attr, li)

        return fix_ampersands(GET.urlencode())


"""
mark_current_links
==================
Detects and earmarks "current" links with the wrapped content.

    {% mark_current_links "active" %}
        <nav>
           <a href="{% url 'home' %}">Home</a>
           <a href="{% url 'content:index' %}">Content</a>
           <a href="{% url 'about' %}">About</a>
        </nav>
    {% endmark_current_links %}

Argument is optional; defaults to "current". A css class with this name will
be added to the link if the current request matches the href URL. URLs longer
than a single character (i.e. "/") use startswith matching, so that
/content/blah/ will match /content/.

TODO:
- Detect existing "class" attributes and append to that if found
  (using a markup parsing library)
- Some clever configuration to detect/support multiple links which share
  a common prefix.

"""
@register.tag(name='mark_current_links')
def do_mark_current_links(parser, token):
    tokens = token.split_contents()
    tag_name = tokens.pop(0)
    css_class = 'current'
    if len(tokens) == 1:
        css_class = tokens[1]
    elif len(tokens) > 1:
        raise template.TemplateSyntaxError(
            "'%s' node takes only a single optional argument" % tag_name)
    nodelist = parser.parse(('endmark_current_links',))
    parser.delete_first_token()
    return MarkCurrentLinksNode(nodelist, css_class)

class MarkCurrentLinksNode(template.Node):
    def __init__(self, nodelist, css_class):
        self.nodelist = nodelist
        self.css_class = css_class

    def render(self, context):
        output = self.nodelist.render(context)
        current_url = context['request'].path
        def replace_attributes(match):
            attributes = match.group()
            url = match.groupdict()['url']
            if (current_url == url or
                len(url) > 1 and current_url.startswith(url)):
                attributes += ' class="%s"' % self.css_class
            return attributes
        return re.sub(r'href="(?P<url>[^"]+)"', replace_attributes, output)


def _admin_link(tag_name, link_type, context, **kwargs):
    try:
        request = context['request']
    except KeyError:
        if settings.DEBUG:
            raise ImproperlyConfigured(
                '{%% %s %%} requires the request to be accessible '
                'within the template context; perhaps install '
                'django.core.context_processors.request?' % tag_name
            )
        else:
            return ''

    if (
        not hasattr(request, 'user') or
        not request.user.is_authenticated() or
        not request.user.is_staff
    ):
        return ''

    model = kwargs.get('model')

    # TODO: consider trying to lookup AdminSite._registry and checking
    # permissions on ModelAdmin itself -- but how to find the non-standard
    # admin site objects? Registered via admin?
    if not request.user.has_perm(
        '%s.%s_%s' % (
            link_type,
            model._meta.app_label,
            model._meta.module_name,
        )
    ):
        return ''

    admin_namespace = kwargs.pop('admin_namespace', 'admin')
    # TODO: i18n
    link_text = kwargs.pop('link_text').replace(
        '<verbose_name>',
        unicode(model._meta.verbose_name)
    )

    querystring_dict = QueryDict('', mutable=True)
    querystring_dict['_return_url'] = request.path

    for key in kwargs:
        QUERYSTRING_PREFIX = 'querystring_'
        if key.startswith(QUERYSTRING_PREFIX):
            querystring_dict[key[len(QUERYSTRING_PREFIX):]] = kwargs.get(key)
    querystring = querystring_dict.urlencode()

    return '<a href="%s%s" class="admin-link">%s</a>' % (
        reverse(
            '%s:%s_%s_%s' % (
                admin_namespace,
                model._meta.app_label,
                model._meta.module_name,
                link_type,
            ),
            args=kwargs.pop('reverse_args', ()),
            kwargs=kwargs.pop('reverse_kwargs', {}),
        ),
        ('?%s' % querystring) if querystring else '',
        link_text,
    )


@register.simple_tag(takes_context=True)
def add_link(context, model_string, **kwargs):
    model = get_model(*model_string.split('.'))
    if model is None:
        if settings.DEBUG:
            raise ImproperlyConfigured(
                '{%% add_link "%s" %%} -- model cannot be found' % (
                    model_string,
                )
            )
        else:
            return ''

    defaults = {
        'link_text': 'Add <verbose_name>',
        'model': model,
    }
    defaults.update(**kwargs)
    return _admin_link('add_link', 'add', context, **defaults)


@register.simple_tag(takes_context=True)
def change_link(context, obj, **kwargs):
    defaults = {
        'link_text': 'Edit this <verbose_name>',
        'model': obj.__class__,
        'reverse_args': (obj.pk,),
    }
    defaults.update(**kwargs)
    return _admin_link('change_link', 'change', context, **defaults)
