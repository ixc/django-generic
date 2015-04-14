from django.contrib import admin

from generic.admin.actions import csv


class CSVExportAdmin(admin.ModelAdmin):
    """
    Legacy admin mixin for CSV export support.

    Use generic.admin.actions.csv.CSVExportAction instead.
    """

    _csv_export = csv.CSVExportAction()

    def get_actions(self, request):
        actions = super(CSVExportAdmin, self).get_actions(request)
        if self.csv_export_enabled(request):
            if not 'csv_export' in actions:
                actions['csv_export'] = self.get_action('csv_export')
        else:
            if 'csv_export' in actions:
                del actions['csv_export']
        return actions

    def csv_export_enabled(self, request):
        return bool(self.csv_export_fields(request))

    # Backwards compat methods for model admin classes that have
    # overridden them.

    def csv_export(self, request, queryset):
        return self._csv_export(self, request, queryset)

    def csv_export_stream(self, request, queryset):
        return self._csv_export.csv_export_stream(self, request, queryset)

    def csv_export_fields(self, request):
        return self._csv_export.csv_export_fields(self, request)

    def csv_export_filename(self, request):
        return self._csv_export.csv_export_filename(self, request)
