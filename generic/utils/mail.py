import copy
import logging
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core import mail
from django.template import RequestContext
from django.template.loader import render_to_string
from django.test import RequestFactory
from ..templatetags.generic_tags import html_to_text

logger = logging.getLogger(__name__)

def get_dummy_request():
    dummy_request = RequestFactory().request()
    dummy_request.session = {}
    dummy_request.user = AnonymousUser()
    return dummy_request

class EmailMessage(mail.EmailMessage):
    """ Generic feature additions to the standard EmailMessage """
    def __init__(self, *args, **kwargs):
        # template-rendering shortcuts:
        self.template_name = kwargs.pop('template_name', None)
        self.context = kwargs.pop('context', None)
        self.request = kwargs.pop('request', get_dummy_request())
        self.use_context_processors = kwargs.pop(
            'use_context_processors', True)

        super(EmailMessage, self).__init__(*args, **kwargs)

        if self.template_name and not self.body:
            if self.use_context_processors:
                context = RequestContext(self.request)
                context.update(self.context)
            else:
                context = self.context
            self.body = render_to_string(self.template_name, context)

    def send_separately(self, fail_silently=False):
        # where there are multiple recipients in the 'to' field, send
        # each one as a separate email to avoid exposing third-party addresses
        messages = []
        for address in self.to:
            message = copy.copy(self) # no need for deepcopy here?
            message.to = [address]
            messages.append(message)
        return self.get_connection(fail_silently).send_messages(messages)


class FallbackEmailMessage(EmailMessage):
    """ EmailMessage which sends to settings.ADMINS if found recipientless """
    def __init__(self, *args, **kwargs):
        self.fallback_addresses = kwargs.pop('fallback_addresses', None)
        self.fallback_prefix = kwargs.pop('fallback_prefix', '[Fallback] ')
        self.fallback_body_prefix = kwargs.pop(
            'fallback_body_prefix', (
                'WARNING: this message has been sent to ADMINS because the '
                'intended recipient list was empty.'
            )
        )
        super(FallbackEmailMessage, self).__init__(*args, **kwargs)

    def get_fallback_addresses(self):
        if self.fallback_addresses is None:
            return dict(settings.ADMINS).values()
        else:
            return self.fallback_addresses

    def send(self, fail_silently=False):
        if not self.recipients():
            self.send_separately = False
            if not self.fallback_addresses:
                logger.error(
                    'No fallback recipients for message: %s' % self.subject)
            self.to = self.fallback_addresses
            self.subject = u''.join([self.fallback_prefix, self.subject])
            self.body = u'\n'.join([self.fallback_body_prefix, self.body])
        return super(FallbackEmailMessage, self).send(fail_silently)


class TemplateEmail(mail.EmailMultiAlternatives):
    base_body_template = 'generic/email/body.txt'
    base_subject_template = 'generic/email/subject.txt'
    base_html_template = 'generic/email/body.html'

    def __init__(self, template_name, context=None, **kwargs):
        self.template_name = template_name
        self.context = context or {}
        self.request = kwargs.pop('request', get_dummy_request())
        self.process_context = kwargs.pop('process_context', True)

        super(TemplateEmail, self).__init__(**kwargs)

        if self.template_name:
            self.body = self.body or self.render_body()
            self.subject = self.subject or self.render_subject()
            html = self.render_html()
            if html.strip():
                self.attach_alternative(html, 'text/html')
                if not self.body.strip():
                    self.body = html_to_text(html)

    def _get_context(self, base_template):
        if self.process_context:
            context = RequestContext(self.request)
            context.update(self.context)
        else:
            context = self.context
        context['base_template'] = base_template
        return context

    def render_body(self):
        return render_to_string(
            self.template_name,
            self._get_context(self.base_body_template)
        )

    def render_subject(self):
        return render_to_string(
            self.template_name,
            self._get_context(self.base_subject_template)
        ).replace('\n', ' ').strip() # enforce single-line

    def render_html(self):
        return render_to_string(
            self.template_name,
            self._get_context(self.base_html_template)
        )
