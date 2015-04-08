This app contains some Django template tags, middleware, context processors,
etc. of various kinds that will make your life easier in almost every project.
To avoid turning this app into something too messy, one has to be quite strict
before adding things into it. Please only contribute things that could be used
in most projects, that do not already exist in other apps.

Also note that things might be taken out of this package at some stage if they
find a better home.

Running tests
-------------

Create a virtual envrionment and install the project with test support
using pip:

    virtualenv venv
    source venv/bin/activate
    pip install -e .[test]

Then run the tests from the project root directory:

    cd test_site
    ./manage.py test
