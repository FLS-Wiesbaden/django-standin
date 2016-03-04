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

# Contains app specific settings!
from django.conf import settings
from django.db.models import BooleanField
from django.utils.translation import ugettext_lazy as _

PLAN_FILES_ENCODING = getattr(settings, 'PLAN_FILES_ENCODING', 'utf-8')
PLAN_PARSER_MODEL = getattr(settings, 'PLAN_PARSER_MODEL', 'standin.parser.DavinciJsonParser')
PLAN_PARSER_REGEX_MOVED_TO = getattr(settings, 'PLAN_PARSER_REGEX_MOVED_TO', '^Auf (?P<day>[0-9]{1,2})\.(?P<month>[0-9]{1,2})\. (?P<weekday>[a-zA-Z]{2}) (?P<startHour>[0-9]{1,2})(-(?P<endHour>[0-9]{1,2}))? verschoben$')
PLAN_PARSER_REGEX_MOVED_FROM = getattr(settings, 'PLAN_PARSER_REGEX_MOVED_TO', '^Von (?P<day>[0-9]{1,2})\.(?P<month>[0-9]{1,2})\. (?P<weekday>[a-zA-Z]{2}) (?P<startHour>[0-9]{1,2})(-(?P<endHour>[0-9]{1,2}))? verschoben$')
PLAN_PUPIL_TEACHER_FULLNAME = getattr(settings, 'PLAN_PUPIL_TEACHER_FULLNAME', False)
PLAN_PUPIL_TEACHER_SHORTCUT = getattr(settings, 'PLAN_PUPIL_TEACHER_SHORTCUT', False)
PLAN_PUPIL_SUBJECT_FULLNAME = getattr(settings, 'PLAN_PUPIL_SUBJECT_FULLNAME', False)
PLAN_PUPIL_SUBJECT_SHORTCUT = getattr(settings, 'PLAN_PUPIL_SUBJECT_SHORTCUT', False)

def get(name):
	if hasattr(name, 'get_value'):
		return getattr(name, 'get_value')()
	else:
		return name

# to allow to edit it online:
# To be sure our app is still functional without django-siteprefs
# we use this try-except block.
try:
	from siteprefs.toolbox import patch_locals, register_prefs, pref_group, pref
	patch_locals()  # This bootstrap is required before `register_prefs` step.

	# And that's how we expose our options to Admin.
	register_prefs(
		pref_group(
			_('Standin parser settings'), (
				PLAN_FILES_ENCODING, PLAN_PARSER_MODEL, PLAN_PARSER_REGEX_MOVED_TO, PLAN_PARSER_REGEX_MOVED_FROM
			), 
			static=False
		),
		pref(
			PLAN_PUPIL_TEACHER_FULLNAME, 
			field=BooleanField(), 
			static=False,
			verbose_name=_('Show full name of teachers'),
			category=_('Standin pupil view')
		),
		pref(
			PLAN_PUPIL_TEACHER_SHORTCUT, 
			field=BooleanField(), 
			static=False,
			verbose_name=_('Show abbreviation of teachers'),
			help_text=_('This setting has only an affect if the full name of teachers are shown. In this case, the teachers abbreviation is appended in brackets.'),
			category=_('Standin pupil view')
		),
		pref(
			PLAN_PUPIL_SUBJECT_FULLNAME, 
			field=BooleanField(), 
			static=False,
			verbose_name=_('Show full title of subject'),
			category=_('Standin pupil view')
		),
		pref(
			PLAN_PUPIL_SUBJECT_SHORTCUT, 
			field=BooleanField(), 
			static=False,
			verbose_name=_('Show abbreviation of subjects'),
			help_text=_('This setting has only an affect if the full title of subjects are shown. In this case, the subject abbreviation is appended in brackets.'),
			category=_('Standin pupil view')
		),
	)
except ImportError:
    pass
