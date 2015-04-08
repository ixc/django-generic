from django.contrib import admin
from generic.admin.mixins import csv

from test_app import models


class CsvTestAdmin(csv.CSVExportAdmin, admin.ModelAdmin):

    pass


admin.site.register(models.CsvTest, CsvTestAdmin)
