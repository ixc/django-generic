import setuptools

tests_require=[
    'webtest',
    'django>=1.6,<1.7a',
    'django-webtest',
    'django-dynamic-fixture',
]

setuptools.setup(
    name='django-generic',
    version='0.1',
    description='Generic Django Utilities',
    author='Simon Meers',
    author_email='simon@simonmeers.com',
    packages=setuptools.find_packages(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Django',],
    include_package_data=True,
    install_requires=[
        'django>=1.6',
    ],
    tests_require=tests_require, # `setuptools test`
    extras_require={
        "test": tests_require # `pip install -e .[test]`
    },
)
