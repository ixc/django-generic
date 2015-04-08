from django.db import models


class CsvTest(models.Model):

    field_one = models.CharField(max_length=200)
    field_two = models.IntegerField(null=True, blank=True)
