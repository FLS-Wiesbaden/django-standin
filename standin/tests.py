# -*- coding: utf-8 -*-
# vim: fenc=utf-8:ts=8:sw=8:si:sta:noet
#
# Standin plan as extension to Django framework.
# Copyright (C) 2016 Friedrich-List-Schule Wiesbaden
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the 
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from django.test import TestCase
from django.conf import settings, global_settings
import os, sys

# Create your tests here.

def main():
    current_dir = os.path.dirname(__file__)
    app_name = os.path.basename(current_dir)
    sys.path.insert(0, os.path.join(current_dir, '..'))

    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=('django.contrib.auth', 'django.contrib.contenttypes', 'django.contrib.admin', app_name),
            DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3'}},
            MIDDLEWARE_CLASSES=global_settings.MIDDLEWARE_CLASSES,  # Prevents Django 1.7 warning.
        )

    try:  # Django 1.7 +
        from django import setup
        setup()
    except ImportError:
        pass

    from django.test.utils import get_runner
    runner = get_runner(settings)()
    failures = runner.run_tests((app_name,))

    sys.exit(failures)


if __name__ == '__main__':
    main()

