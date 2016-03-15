import setuptools

setuptools.setup(
    name='django-generic',
    use_scm_version={'version_scheme': 'post-release'},
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
    install_requires=[],
    setup_requires=['setuptools_scm'],
    include_package_data=True)
