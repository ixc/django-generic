from django import http
from django.contrib import admin
from django.core.urlresolvers import reverse
from django.shortcuts import redirect

class ChangeLinkInline(admin.TabularInline):
    """
    Base class for inlines which link to change forms for further editing.

    Simple workaround for "deep" admin interfaces which would otherwise
    require "nested inlines". See https://code.djangoproject.com/ticket/9025

    Generally useful in conjunction with ChangeFormOnlyAdmin below.
    """

    readonly_fields = ('change_link',)
    change_link_text = 'Click to edit'
    change_link_unsaved_text = 'Not yet saved'

    def change_link(self, obj):
        if obj.id is None:
            return self.change_link_unsaved_text
        return '<a href="%s">%s</a>' % (
            reverse(
                'admin:%s_%s_change' % (
                    obj._meta.app_label,
                    obj._meta.module_name,
                ),
                args=(obj.id,),
                current_app=self.admin_site.name,
            ),
            self.change_link_text,
        )
    change_link.allow_tags = True
    change_link.short_description = 'Edit'


class ChangeFormOnlyAdmin(admin.ModelAdmin):
    """
    For models which don't require an independent change list.

    Generally used with ChangeLinkInline (above) where the inlines on the
    parent object basically act as the change-list.
    """
    def has_change_permission(self, request, obj=None):
        if obj is None:
            return False
        return super(
            ChangeFormOnlyAdmin, self).has_change_permission(request, obj)

    def changelist_view(self, request, extra_context=None):
        # e.g. if you click on a breadcrumb link
        return redirect('..')

    def has_add_permission(self, request):
        return False

    def get_parent(self, obj, request):
        """ Override this method to auto-return on post-save """
        return None

    def response_post_save_change(self, request, obj):
        parent = self.get_parent(obj, request)
        if parent:
            return http.HttpResponseRedirect(
                reverse(
                    'admin:%s_%s_change' % (
                        parent._meta.app_label,
                        parent._meta.module_name,
                    ),
                    args=(parent.pk,),
                    current_app=self.admin_site.name
                )
            )
        return super(
            ChangeFormOnlyAdmin, self).response_post_save_change(request, obj)
