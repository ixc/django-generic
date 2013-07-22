from django import forms
from django import http
from django.contrib import admin
from django.contrib.admin.filters import SimpleListFilter
from django.db.models import loading
from django.utils.translation import ugettext_lazy as _

def get_subclass_choices(parent_model):
    title_if_lower = lambda s: (s.title() if s == s.lower() else s)
    return sorted(
        map(
            lambda model: (
                model._meta.module_name,
                title_if_lower(model._meta.verbose_name),
            ),
            filter(
                lambda model: (
                    issubclass(model, parent_model) and
                    parent_model in model._meta.parents
                ),
                loading.get_models()
            )
        )
    )

class SubclassFilter(SimpleListFilter):
    title = _('Type')
    parameter_name = 'type'

    def lookups(self, request, model_admin):
        return get_subclass_choices(model_admin.model)

    def queryset(self, request, queryset):
        if self.value():
            return queryset.complex_filter(
                {'%s__isnull' % self.value(): False})
        else:
            return queryset


class PolymorphicAdmin(admin.ModelAdmin):
    """
    For use with django-model-utils' InheritanceManager.
    """

    list_filter = (SubclassFilter,)
    subclass_parameter_name = '__subclass'
    subclass_label = _('Type')

    def add_view(self, request, form_url='', extra_context=None):
        if self.subclass_parameter_name in request.POST:
            return http.HttpResponseRedirect(
                '?%s=%s' % (
                    self.subclass_parameter_name,
                    request.POST.get(self.subclass_parameter_name),
                )
            )
        return super(PolymorphicAdmin, self).add_view(
            request, form_url=form_url, extra_context=extra_context)

    def get_fieldsets(self, request, obj=None):
        if not self.get_model(request, obj):
            # show subclass selection field only
            return (
                (None, {'fields': (self.subclass_parameter_name,)},),
            )
        return self.get_modeladmin(request, obj).get_fieldsets(request, obj)

    def get_readonly_fields(self, request, obj=None):
        model_admin = self.get_modeladmin(request, obj)
        return model_admin.get_readonly_fields(request, obj)

    def get_inline_instances(self, request, obj=None):
        model_admin = self.get_modeladmin(request, obj)
        return model_admin.get_inline_instances(request, obj)

    def get_formsets(self, request, obj=None):
        if not self.get_model(request, obj):
            return () # hide inlines on add form until subclass selected
        model_admin = self.get_modeladmin(request, obj)
        return model_admin.get_formsets(request, obj)

    def get_form(self, request, obj=None, **kwargs):
        model_admin = self.get_modeladmin(request, obj)
        form_class = model_admin.get_form(request, obj=obj, **kwargs)
        if not self.get_model(request, obj):
            return self._build_subclass_selection_form(form_class)
        else:
            return form_class

    def get_model(self, request, obj=None):
        return obj.__class__ if obj else (
            loading.get_model(
                self.opts.app_label,
                request.REQUEST.get(self.subclass_parameter_name, '')
            )
        )

    def get_modeladmin(self, request, obj=None):
        model = self.get_model(request, obj)
        if model and model != self.model:
            return self.admin_site._registry.get(
                model, # use registered admin if it exists...
                self.get_unregistered_admin_classes().get(
                    model, # or unregistered one if we know about it
                    self.__class__ # ...or build a generic one
                )(model, self.admin_site)
            )
        else:
            return super(PolymorphicAdmin, self)

    def get_unregistered_admin_classes(self):
        return {
            # override with Model: ModelAdmin mapping
        }

    def _build_subclass_selection_form(self, form_class):
        class SubclassSelectionForm(form_class):
            def __init__(form, *args, **kwargs):
                super(SubclassSelectionForm, form).__init__(*args, **kwargs)
                form.fields[self.subclass_parameter_name] = forms.ChoiceField(
                    choices=get_subclass_choices(self.model),
                    label=self.subclass_label,
                )
        return SubclassSelectionForm

    # TODO: disable bulk deletion action when heterogeneous classes selected
    # -- collector doesn't cope, and raises AttributeErrors

    def queryset(self, request):
        return self.model.objects.select_subclasses()
