import logging

from django import http
from django.contrib import admin
from django.template import defaultfilters
from django.utils.translation import ugettext_lazy as _
from ...utils import unicode_csv

logger = logging.getLogger(__name__)

class CSVExportAdmin(admin.ModelAdmin):

    csv_export_stream_threshold = 500

    def _get_url_name(self, view_name, include_namespace=True):
        return '%s%s_%s_%s' % (
            'admin:' if include_namespace else '',
            self.model._meta.app_label,
            self.model._meta.model_name,
            view_name,
        )

    def csv_export(self, request, queryset):
        encoding = 'utf-8'
        def generate_csv():
            writer = unicode_csv.RowWriter(encoding=encoding)
            fields = self.csv_export_fields(request)
            yield writer.writerow([title for title, key in fields])

            # TODO: detect absence of callables and use efficient .values query
            for obj in queryset:
                row = []
                for title, key in fields:
                    if callable(key):
                        row.append(key(obj))
                    else:
                        row.append(getattr(obj, key))
                yield writer.writerow(row)

        if self.csv_export_stream(request, queryset):
            logger.debug("Streaming CSV response")
            response = http.StreamingHttpResponse(generate_csv())
        else:
            logger.debug("Buffering CSV response")
            response = http.HttpResponse(''.join(generate_csv()))
        response['Content-Type'] = 'text/csv; charset={}'.format(encoding)
        response['Content-Disposition'] = 'attachment; filename={0}'.format(
            self.csv_export_filename(request)
        )
        return response

    def get_actions(self, request):
        actions = super(CSVExportAdmin, self).get_actions(request)
        if self.csv_export_enabled(request):
            if not 'csv_export' in actions:
                actions['csv_export'] = self.get_action('csv_export')
        else:
            if 'csv_export' in actions:
                del actions['csv_export']
        return actions
    csv_export.short_description = _('Export selected items in CSV format')

    def csv_export_enabled(self, request):
        return bool(self.csv_export_fields(request))

    def csv_export_stream(self, request, queryset):
        return queryset.count() >= self.csv_export_stream_threshold

    def csv_export_fields(self, request):
        """
        Returns a list of two-tuples describing the fields to export.

        The first element of each tuple is the label for the column.
        The second element is a field name or callable which will return the
        appropriate value for the field given a model instance.

        By default, uses get_list_display() to determine the fields to
        include, so that the CSV file contains the data shown in the
        admin change list.

        """
        fields = []

        def callable_label(callible):
            if hasattr(field, 'short_description'):
                label = field.short_description
            else:
                label = field.__name__

        for column in self.get_list_display(request):
            label = str(column)
            field = column
            if isinstance(column, basestring):
                # is it a field of the model?
                if column in self.model._meta.fields:
                    label = self.model._meta.fields[column].verbose_name
                # is it an attribute of this admin view?
                elif hasattr(self, column):
                    field = getattr(self, column)
                    label = callable_label(field)
                # is it an attribute of the model?
                elif hasattr(self.model, column):
                    field = getattr(self, self.model)
                    # keep the name as the label

            elif isinstance(field, callable):
                label = callable_label(field)

            fields.append((label, field))
        return fields

    def csv_export_filename(self, request):
        return '{0}.csv'.format(
            defaultfilters.slugify(self.model._meta.verbose_name_plural)
        )
