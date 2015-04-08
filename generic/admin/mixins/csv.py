import io

from django import http
from django.contrib import admin
from django.template import defaultfilters
from django.utils.translation import ugettext_lazy as _
from ...utils import unicode_csv


class CSVExportAdmin(admin.ModelAdmin):
    def _get_url_name(self, view_name, include_namespace=True):
        return '%s%s_%s_%s' % (
            'admin:' if include_namespace else '',
            self.model._meta.app_label,
            self.model._meta.model_name,
            view_name,
        )

    def csv_export(self, request, queryset):
        def generate_csv():
            buf = io.BytesIO()
            writer = unicode_csv.Writer(buf)
            fields = self.csv_export_fields(request)
            writer.writerow([title for title, key in fields])
            yield buf.getvalue()

            # TODO: detect absence of callables and use efficient .values query
            for obj in queryset:
                buf.truncate(0)
                row = []
                for title, key in fields:
                    if callable(key):
                        row.append(key(obj))
                    else:
                        row.append(getattr(obj, key))
                writer.writerow(row)
                yield buf.getvalue()

        response = http.StreamingHttpResponse(generate_csv(), mimetype='text/csv')
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

    def csv_export_fields(self, request):
        """
        This returns a list of two-tuples describing the fields to export.
        The first element of each tuple is the label for the column.
        The second element is a field name or callable which will return the
        appropriate value for the field given a model instance.
        """
        fields = []
        for field in self.model._meta.fields:
            fields.append((field.verbose_name, field.name))
        return fields

    def csv_export_filename(self, request):
        return '{0}.csv'.format(
            defaultfilters.slugify(self.model._meta.verbose_name_plural)
        )
