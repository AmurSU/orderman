try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

setup(
    name='OrderManager',
    version='0.6',
    description='Order (Task, Ticket) Manager for Amur State University',
    author='Novikov "Envek" Andrey, department of program and technical supply, Amur State University',
    author_email='andrey.novikov@amursu.ru',
    url='www.amursu.ru',
    install_requires=[
        "WebOb>=1.0,<=1.0.9",
        "Pylons>=0.9.7",
        "SQLAlchemy>=0.5,<=0.5.9",
        "PyTils>=0.2.3",
        "FormEncode>=1.2.6",
        "WebHelpers>=1.3,<2.0"
    ],
    setup_requires=["PasteScript>=1.6.3"],
    packages=find_packages(exclude=['ez_setup']),
    include_package_data=True,
    test_suite='nose.collector',
    package_data={'ordermanager': ['i18n/*/LC_MESSAGES/*.mo']},
    #message_extractors={'ordermanager': [
    #        ('**.py', 'python', None),
    #        ('templates/**.mako', 'mako', {'input_encoding': 'utf-8'}),
    #        ('public/**', 'ignore', None)]},
    zip_safe=False,
    paster_plugins=['PasteScript', 'Pylons'],
    entry_points="""
    [paste.app_factory]
    main = ordermanager.config.middleware:make_app

    [paste.app_install]
    main = pylons.util:PylonsInstaller
    """,
)
