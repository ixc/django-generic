from django import http
from django.contrib import admin
from django.conf.urls import url
from django.shortcuts import get_object_or_404, redirect

from ...models.delible import Delible
class DelibleAdmin(admin.ModelAdmin):
    """ Admin with "undelete" functionality for Delible objects """
    change_form_template = 'admin/delible_change_form.html'

    def delete_model(self, request, obj):
        if isinstance(obj, Delible):
            obj.delete(request=request)
        else:
            obj.delete()

    def undelete(self, request, pk):
        permission = '%s.delete_%s' % (
            self.model._meta.app_label, self.model._meta.module_name)
        if not request.user.has_perm(permission):
            return http.HttpResponseForbidden()
        else:
            obj = get_object_or_404(self.model, pk=pk)
            try:
                obj.undelete()
            except AttributeError:
                self.message_user(request, 'Error; cannot undelete.')
            else:
                self.message_user(request, u"%s undeleted!" % obj)
            return redirect(
                'admin:%s_%s_change' % (
                    obj._meta.app_label, obj._meta.module_name), obj.pk)

    def get_urls(self):
        urls = super(DelibleAdmin, self).get_urls()
        if issubclass(self.model, Delible):
            urls = [
                url(
                    r'^(?P<pk>.+)/undelete/$',
                    self.admin_site.admin_view(self.undelete),
                    name='%s_%s_undelete' % (
                        self.model._meta.app_label,
                        self.model._meta.model_name)
                )
            ] + urls
        return urls

