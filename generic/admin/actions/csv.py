import logging

from django import http
from django.template import defaultfilters
from django.utils.translation import ugettext_lazy as _

from generic.utils import unicode_csv


logger = logging.getLogger(__name__)


class CSVExportAction(object):
    """A model admin CSV Export action.

    This action allows you to define one or more CSV export admin
    actions. To use it to export visible columns in the admin change
    kist view, add the the following to your admin class:

        csv_export = CSVExportAction()
        actions = ('csv_export',)

    To customise the columns exported, extend this class, override
    csv_export_fields, and use that custom subclass as in the example
    above:

        class MyCustomCsv(CSVExportAction):

            short_description = _('Export selected item names as CSV')

            def csv_export_fields(self, modeladmin, request):
                return (
                    ('Object Id', 'id'),
                    ('Name', 'name'),
                )

        custom_csv = MyCustomCsv()
        actions = ('custom_csv',)

    Of course, these can be combined:

        csv_export = CSVExportAction()
        custom_csv = MyCustomCsv()
        actions = ('csv_export', 'custom_csv')

    """

    short_description = _('Export selected items in CSV format')
    csv_export_stream_threshold = 500

    def __call__(self, modeladmin, request, queryset):
        encoding = 'utf-8'
        def generate_csv():
            writer = unicode_csv.RowWriter(encoding=encoding)
            fields = self.csv_export_fields(modeladmin, request)
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

        if self.csv_export_stream(modeladmin, request, queryset):
            logger.debug("Streaming CSV response")
            response = http.StreamingHttpResponse(generate_csv())
        else:
            logger.debug("Buffering CSV response")
            response = http.HttpResponse(''.join(generate_csv()))
        response['Content-Type'] = 'text/csv; charset={}'.format(encoding)
        response['Content-Disposition'] = 'attachment; filename={0}'.format(
            self.csv_export_filename(modeladmin, request)
        )
        return response

    def csv_export_stream(self, modeladmin, request, queryset):
        return queryset.count() >= self.csv_export_stream_threshold

    def csv_export_fields(self, modeladmin, request):
        """
        Returns a list of two-tuples describing the fields to export.

        The first element of each tuple is the label for the column.
        The second element is a field name or callable which will return the
        appropriate value for the field given a model instance.

        By default, uses get_list_display() to determine the fields to
        include, so that the CSV file contains the data shown in the
        admin change list.

        """
        model = modeladmin.model
        fields = []

        def callable_label(callible):
            return (
                field.short_description
                if hasattr(field, 'short_description')
                else field.__name__
            )

        for column in modeladmin.get_list_display(request):
            label = str(column)
            field = column

            if isinstance(column, basestring):
                # is it a field of the model?
                if column in model._meta.fields:
                    label = model._meta.fields[column].verbose_name
                # is it an attribute of the model?
                elif hasattr(model, column):
                    field = getattr(model, column)
                    if column == '__str__':
                        label = str(model._meta.verbose_name)
                # is it an attribute of this admin view?
                elif hasattr(modeladmin, column):
                    field = getattr(modeladmin, column)
                    label = callable_label(field)

            elif isinstance(field, callable):
                label = callable_label(field)

            fields.append((label, field))

        return fields

    def csv_export_filename(self, modeladmin, request):
        return '{0}.csv'.format(
            defaultfilters.slugify(modeladmin.model._meta.verbose_name_plural)
        )
