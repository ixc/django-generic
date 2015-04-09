from django import http
from django.conf import settings
from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured

from django.core.urlresolvers import reverse
from ..widgets import (
    ForeignKeyCookedIdWidget,
    ManyToManyCookedIdWidget,
    TabularInlineForeignKeyCookedIdWidget,
    TabularInlineManyToManyCookedIdWidget,
    StackedInlineForeignKeyCookedIdWidget,
    StackedInlineManyToManyCookedIdWidget,
)

try:
    from django.conf.urls import patterns, url
except ImportError:
    from django.conf.urls.defaults import patterns, url

try:
    import json
except ImportError:
    from django.utils import simplejson as json

class BaseCookedIdAdmin:
    """
    Support for CookedIdWidgets (vs. RawIdWidgets) in admin.

    See:
    - `generic.admin.widgets.ManyToManyCookedIdWidget`, and
    - `generic.admin.widgets.ForeignKeyCookedIdWidget`

    Simply list fields in self.cooked_id_widgets instead of self.raw_id_widgets

    Override self.cook() to customise cooked object representations.
    """
    cooked_id_fields = ()

    def cook(self, obj, request, field_name):
        """
        Override this to customise the "cooked" representation of objects
        """
        view_url = ''
        edit_url = ''

        if hasattr(obj, 'get_absolute_url'):
            view_url = obj.get_absolute_url();
        if request.user.has_perm('%s.change_%s' %(obj._meta.app_label, obj._meta.module_name)):
			edit_url = reverse('admin:%s_%s_change' %(obj._meta.app_label,  obj._meta.module_name),  args=[obj.id])

        result = {'text': unicode(obj),
                  'view_url': view_url,
                  'edit_url': edit_url
                  }
        return result

    def cook_ids(self, request, pk, field_name, raw_ids):
        # TODO: extend to support non-integer/non-`id` PKs
        if not field_name in self.cooked_id_fields:
            raise http.Http404
        try:
            ids = map(int, raw_ids.split(','))
        except ValueError:
            if raw_ids == '':
                ids = []
            else:
                raise http.Http404
        target_model_admin = self.admin_site._registry.get(
            self.model._meta.get_field(field_name).rel.to)
        response_data = {}
        if (
                target_model_admin and
                target_model_admin.has_change_permission(request)
        ):
            for obj in target_model_admin.queryset(request).filter(id__in=ids):
                response_data[obj.pk] = self.cook(
                    obj, request=request, field_name=field_name)
        else:
            pass # graceful-ish.
        return http.HttpResponse(
            json.dumps(response_data), mimetype='application/json')

    def assert_cooked_target_admin(self, db_field):
        if db_field.rel.to in self.admin_site._registry:
            return True
        else:
            if settings.DEBUG:
                raise ImproperlyConfigured(
                    "%s.cooked_id_fields contains '%r', but %r "
                    "is not registed in the same admin site." % (
                        self.__class__.__name__,
                        db_field.name,
                        db_field.rel.to,
                    )
                )
            else:
                pass # fail silently


class CookedIdAdmin(BaseCookedIdAdmin, admin.ModelAdmin):

    def cook_ids_inline(self, request, model_name, field_name, raw_ids):

        # find the correct inline instance and pass control to it's own cook_ids()
        inlines = self.get_inline_instances(request)
        for inline in inlines:
            content_type = ContentType.objects.get_for_model(inline.model)
            if model_name == content_type.model and field_name in inline.cooked_id_fields:
                # this is our guy
                return inline.cook_ids(request, field_name, raw_ids)

        raise http.Http404

    def get_urls(self):

        urlpatterns = patterns(
            '',
            url(r'^(?P<pk>.+)/cook-ids/(?P<field_name>\w+)/(?P<raw_ids>[\d,]+)/$',
                self.admin_site.admin_view(self.cook_ids))
        )

        # add any inline cooked ID urls...

        for inline in self.inlines:
            try:
                if inline.cooked_id_fields:
                    content_type = ContentType.objects.get_for_model(inline.model)
                    urlpatterns += patterns(
                        '',
                        url(r'^cook-ids-inline/(?P<model_name>'+content_type.model+')/(?P<field_name>\w+)/(?P<raw_ids>[\d,]+)/$',
                            self.admin_site.admin_view(self.cook_ids_inline))
                    )
            except AttributeError:
                # probably not a TabularInlineCookedIdAdmin
                pass

        return urlpatterns + super(CookedIdAdmin, self).get_urls()

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        if db_field.name in self.cooked_id_fields:
            if self.assert_cooked_target_admin(db_field):
                kwargs['widget'] = ManyToManyCookedIdWidget(
                    db_field.rel, self.admin_site)
        return super(CookedIdAdmin, self).formfield_for_manytomany(
            db_field, request=request, **kwargs)

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if db_field.name in self.cooked_id_fields:
            if self.assert_cooked_target_admin(db_field):
                kwargs['widget'] = ForeignKeyCookedIdWidget(
                    db_field.rel, self.admin_site)
        return super(CookedIdAdmin, self).formfield_for_foreignkey(
            db_field, request=request, **kwargs)


class TabularInlineCookedIdAdmin(BaseCookedIdAdmin, admin.TabularInline):

    content_type = None

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        content_type = ContentType.objects.get_for_model(self.model)
        if db_field.name in self.cooked_id_fields:
            if self.assert_cooked_target_admin(db_field):
                kwargs['widget'] = TabularInlineManyToManyCookedIdWidget(
                    db_field.rel, self.admin_site, {
                        'data-model': content_type.model,
                        'data-field': db_field.name,
                    })
        return super(TabularInlineCookedIdAdmin, self).formfield_for_manytomany(
            db_field, request=request, **kwargs)

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        content_type = ContentType.objects.get_for_model(self.model)
        if db_field.name in self.cooked_id_fields:
            if self.assert_cooked_target_admin(db_field):
                kwargs['widget'] = TabularInlineForeignKeyCookedIdWidget(
                    db_field.rel, self.admin_site, {
                        'data-model': content_type.model,
                        'data-field': db_field.name,
                    })
        return super(TabularInlineCookedIdAdmin, self).formfield_for_foreignkey(
            db_field, request=request, **kwargs)


class StackedInlineCookedIdAdmin(BaseCookedIdAdmin, admin.StackedInline):

    content_type = None

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        content_type = ContentType.objects.get_for_model(self.model)
        if db_field.name in self.cooked_id_fields:
            if self.assert_cooked_target_admin(db_field):
                kwargs['widget'] = StackedInlineManyToManyCookedIdWidget(
                    db_field.rel, self.admin_site, {
                        'data-model': content_type.model,
                        'data-field': db_field.name,
                    })
        return super(StackedInlineCookedIdAdmin, self).formfield_for_manytomany(
            db_field, request=request, **kwargs)

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        content_type = ContentType.objects.get_for_model(self.model)
        if db_field.name in self.cooked_id_fields:
            if self.assert_cooked_target_admin(db_field):
                kwargs['widget'] = StackedInlineForeignKeyCookedIdWidget(
                    db_field.rel, self.admin_site, {
                        'data-model': content_type.model,
                        'data-field': db_field.name,
                    })
        return super(StackedInlineCookedIdAdmin, self).formfield_for_foreignkey(
            db_field, request=request, **kwargs)
