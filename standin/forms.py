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

from django import forms
from standin.models import Plan
from django.utils.translation import ugettext_lazy as _

class PlanUploadForm(forms.Form):
	"""Creates admin form to upload a plan manually.

	But independent of the model, because of the upload form.
	"""

	plan = forms.FileField(required=True, label=_('Upload plan'))

	def save(self):
		# we need to find a parser for the file!
		pass

