import io

from django.core import urlresolvers
from django.contrib.auth.models import User
from django.test import TestCase
from django_dynamic_fixture import G
from django_webtest import WebTest

from generic.utils import unicode_csv
from test_app import models


class CsvRowWriterTestCase(TestCase):

    def setUp(self):
        self.writer = unicode_csv.RowWriter()

    def test_writerow(self):
        row = self.writer.writerow(['hello', '1'])
        self.assertEqual(row, 'hello,1\r\n')


class CsvWriterTestCase(TestCase):

    def setUp(self):
        self.out = io.BytesIO()
        self.writer = unicode_csv.Writer(self.out)

    def test_writerow(self):
        self.writer.writerow(['hello', '1'])
        self.assertEqual(self.out.getvalue(), 'hello,1\r\n')

    def test_writerows(self):
        self.writer.writerows([
            ['hello', '1'],
            ['there', '2'],
        ])
        self.assertEqual(
            self.out.getvalue(),
            'hello,1\r\nthere,2\r\n'
        )


class CSVExportAdminTestCase(WebTest):

    def setUp(self):
        self.username = 'admin'
        self.password = 'password'
        self.superuser = User.objects.create_superuser(
            self.username, 'example@test.com', self.password
        )
        self.superuser.save()

        login_response = self.app.get(urlresolvers.reverse('admin:index'))
        login_form = login_response.forms[0]
        login_form['username'] = self.username
        login_form['password'] = self.password
        self.login_response = login_form.submit().follow()

        self.test_url = urlresolvers.reverse('admin:test_app_csvtest_changelist')
        self.fixtures = [ G(models.CsvTest) ]

    def tearDown(self):
        self.superuser.delete()

    def test_get_contains_csv_action(self):
        response = self.app.get(
            self.test_url,
            dict(action='csv_export'),
            user=self.superuser
        ).maybe_follow()
        self.assertEqual(200, response.status_code)
        form = response.forms['changelist-form']
        self.assertIn('<option value="csv_export">', form.text)

    def test_response(self):
        response = self.app.get(
            self.test_url,
            dict(action='csv_export'),
            user=self.superuser
        ).maybe_follow()

        form = response.forms['changelist-form']
        form['action'].select('csv_export')
        form['_selected_action'].checked = True

        response = form.submit().maybe_follow()
        self.assertEqual(200, response.status_code)
        self.assertCsvRows(
            response,
            'csv test\r\n',
            'CsvTest object\r\n'
        )

    def assertCsvRows(self, response, *rows):
        body = io.StringIO(response.text)
        for row in rows:
            self.assertEqual(row, body.readline())
