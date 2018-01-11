#!/usr/bin/env python
#
# Copyright (C) 2017 Linaro Limited
#
# Author: Remi Duraffort <remi.duraffort@linaro.org>
#
# This file is part of LAVA Server.
#
# LAVA Server is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3
# as published by the Free Software Foundation
#
# LAVA Server is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with LAVA Server.  If not, see <http://www.gnu.org/licenses/>.

# Created with Django 1.8.18

import imp

# Import application settings
from lava_scheduler_app.settings import *


# Allow only the connection through the reverse proxy
ALLOWED_HOSTS = ['[::1]', '127.0.0.1', 'localhost']

# Application definition
INSTALLED_APPS = [
    # Add LAVA applications
    'lava_server',
    'dashboard_app',
    'lava_results_app',
    'lava_scheduler_app',
    # Add LAVA dependencies
    'django_tables2',
    'linaro_django_xmlrpc',
    'google_analytics',
    # Add contrib
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django.contrib.sites',  # FIXME: should not be needed anymore
]

MIDDLEWARE_CLASSES = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
]

ROOT_URLCONF = 'lava_server.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
                'django.template.context_processors.static',
                # LAVA context processors
                'lava_server.context_processors.lava',
                'lava_server.context_processors.ldap_available',
            ],
        },
    },
]

WSGI_APPLICATION = 'lava_server.wsgi.application'

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = '/static/'


# Automatically install some applications
available_modules = list()
for module_name in ["devserver", "django_extensions", "django_openid_auth", "hijack"]:
    try:
        imp.find_module(module_name)
        INSTALLED_APPS.append(module_name)
    except ImportError:
        pass

# Add google analytics model.
GOOGLE_ANALYTICS_MODEL = True

# General URL prefix
MOUNT_POINT = ""

# Do not disallow any user-agent yet
DISALLOWED_USER_AGENTS = []

# Set a site ID
# FIXME: should not be needed
SITE_ID = 1

# Django System check framework settings for security.* checks.
# Silence some checks that should be explicitly configured by administrators
# on need basis.
SILENCED_SYSTEM_CHECKS = [
    'security.W004',  # silence SECURE_HSTS_SECONDS
    'security.W008',  # silence SECURE_SSL_REDIRECT
]
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = 'DENY'
HTTPS_XML_RPC = True