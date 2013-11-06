#!/usr/bin/env python
#
# Copyright (C) 2010 Linaro Limited
#
# Author: Zygmunt Krynicki <zygmunt.krynicki@linaro.org>
#
# This file is part of LAVA Server.
#
# LAVA Server is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# as published by the Free Software Foundation
#
# LAVA Server is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with LAVA Server.  If not, see <http://www.gnu.org/licenses/>.

from setuptools import setup, find_packages


setup(
    name='lava-server',
    version=":versiontools:lava_server:__version__",
    author="Zygmunt Krynicki",
    author_email="zygmunt.krynicki@linaro.org",
    namespace_packages=['lava', 'lava.utils'],
    packages=find_packages(),
    entry_points=open('entry_points.ini', 'r').read(),
    test_suite="lava_server.tests.run_tests",
    license="AGPL",
    description="LAVA Server",
    long_description="""
    LAVA Server is an application container for various server side
    applications of the LAVA stack. It has an extensible architecture that
    allows to add extra features that live in their own Python packages.  The
    standard LAVA extensions (dashboard and scheduler) are already contained in
    this package.
    """,
    url='https://launchpad.net/lava-server',
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        ("License :: OSI Approved :: GNU Library or Lesser General Public"
         " License (LGPL)"),
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Topic :: Software Development :: Testing",
    ],
    install_requires=[
        'django >= 1.3',
        'django-openid-auth >= 0.2',
        'django-restricted-resource >= 0.2.7',
        "django-tables2 >= 0.9.4",
        'docutils >= 0.6',
        'lava-tool >= 0.2',
        'lava-utils-interface >= 1.0',
        'linaro-django-xmlrpc >= 0.4',
        'python-openid >= 2.2.4',  # this should be a part of
                                   # django-openid-auth deps
        'south >= 0.7.3',
        'versiontools >= 1.8',
        'markdown >= 2.0.3',
        'longerusername',

        # optional dependency; for authentication with Attlassian Crowd SSO
        # 'django-crowd-rest-backend >= 0.3,

        # dashboard
        'linaro-dashboard-bundle >= 1.10',
        'linaro-django-pagination >= 2.0.2',
        'pygments >= 1.2',

        # scheduler
        "lava-dispatcher >= 0.33.2",
        "simplejson",
        "twisted",
    ],
    setup_requires=[
        'versiontools >= 1.8',
    ],
    tests_require=[
        'django-testscenarios >= 0.7.1',
    ],
    zip_safe=False,
    include_package_data=True)
