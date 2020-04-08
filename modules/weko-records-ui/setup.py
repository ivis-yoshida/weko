# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Module for displaying records."""

import os

from setuptools import find_packages, setup

readme = open('README.rst').read()
history = open('CHANGES.rst').read()

tests_require = [
    'check-manifest>=0.25',
    'coverage>=4.0',
    'isort>=4.2.2',
    'pydocstyle>=1.0.0',
    'pytest-cache>=1.0',
    'pytest-cov>=1.8.0',
    'pytest-pep8>=1.0.6',
    'pytest>=2.8.0',
]

extras_require = {
    'docs': [
        'Sphinx>=1.5.1',
    ],
    'tests': tests_require,
}

extras_require['all'] = []
for reqs in extras_require.values():
    extras_require['all'].extend(reqs)

setup_requires = [
    'Babel>=1.3',
    'pytest-runner>=2.6.2',
]

install_requires = [
    'Flask-BabelEx>=0.9.2',
    'invenio-previewer>=1.0.0a11',
    'PyPDF2>=1.26.0',
    'invenio-pidrelations>=1.0.0a3',
    'invenio-records>=1.0.0b4',
]

packages = find_packages()


# Get the version string. Cannot be done with import!
g = {}
with open(os.path.join('weko_records_ui', 'version.py'), 'rt') as fp:
    exec(fp.read(), g)
    version = g['__version__']

setup(
    name='weko-records-ui',
    version=version,
    description=__doc__,
    long_description=readme + '\n\n' + history,
    keywords='weko records ui',
    license='GPLv2',
    author='National Institute of Informatics',
    author_email='wekosoftware@nii.ac.jp',
    url='https://github.com/wekosoftware/weko-records-ui',
    packages=packages,
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    entry_points={
        'invenio_base.apps': [
            'weko_records_ui = weko_records_ui:WekoRecordsUI',
        ],
        'invenio_base.api_apps': [
            'weko_records_ui_cites_rest = weko_records_ui:WekoRecordsCitesREST',
        ],
        'invenio_admin.views': [
            'weko_records_ui_setting = weko_records_ui.admin:item_adminview',
            'weko_records_ui_pdfcoverpage = weko_records_ui.admin:pdfcoverpage_adminview',
            'weko_records_ui_institution = weko_records_ui.admin:institution_adminview',
            'weko_records_ui_bulk_update = weko_records_ui.admin:item_management_bulk_update_adminview',
        ],
        'invenio_i18n.translations': [
            'messages = weko_records_ui',
        ],
        'invenio_config.module': [
            'weko_records_ui = weko_records_ui.config',
        ],
        'invenio_assets.bundles': [
            'weko_records_ui_css = weko_records_ui.bundles:style',
            'weko_records_ui_dependencies_js = weko_records_ui.bundles:js_dependecies',
            'weko_records_ui_js = weko_records_ui.bundles:js',
            'weko_records_ui_preview_carousel_js = weko_records_ui.bundles:preview_carousel',
            'weko_records_ui_file_action_js = weko_records_ui.bundles:file_action_js',
            'weko_records_ui_bootstrap_popover_js = weko_records_ui.bundles:bootstrap_popover_js',
            'weko_records_ui_bootstrap_popover_css = weko_records_ui.bundles:bootstrap_popover_css',
        ],
        'invenio_access.actions': [
            'detail_page_access'
            ' = weko_records_ui.permissions:action_detail_page_access',
            'download_original_pdf_access = weko_records_ui.permissions:action_download_original_pdf_access',
        ],
        'invenio_db.alembic': [
            'weko_records_ui = weko_records_ui:alembic',
        ],
        'invenio_db.models': [
            'weko_records_ui = weko_records_ui.models',
        ],
    },
    extras_require=extras_require,
    install_requires=install_requires,
    setup_requires=setup_requires,
    tests_require=tests_require,
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Development Status :: 1 - Planning',
    ],
)
