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

from django.core.exceptions import PermissionDenied
from django.contrib import admin
from django.contrib.admin import helpers
from django.contrib import messages
from django.shortcuts import redirect
from django.template import RequestContext
from standin.models import SchoolYear, Plan, Teacher, Subject, Division, Grade
from standin.forms import PlanUploadForm
from django.utils.translation import ugettext as _

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
	"""Creates admin interface for all uploaded plans.

	But to add something, only upload is allowed!
	"""
	list_display = ('vpdtup', 'vpstand')

	def add_view(self, request):
		context = RequestContext(request)
		# has user permission?
		if not self.has_add_permission(request):
			raise PermissionDenied

		if request.POST:
			form = PlanUploadForm(request.POST, request.FILES)
			if form.is_valid():
				form.save()
				# Add feedback for the user and return to the newsletter
				# overview page
				messages.add_message(
					request,
					messages.SUCCESS,
					_('Plan uploaded.')
					)
				return redirect('admin:standin_plan_changelist')
		else:
			form = PlanUploadForm()

		obj = None
		formsets, inline_instances = self._create_formsets(request, None, change=False)
		adminForm = helpers.AdminForm(
			form,
			[(None, {'fields': ['plan']})],
			{},
		)
		media = self.media + adminForm.media
		inline_formsets = self.get_inline_formsets(request, formsets, inline_instances, obj)
		for inline_formset in inline_formsets:
			media = media + inline_formset.media

		context = dict(self.admin_site.each_context(request),
			title=_('Upload a new plan'),
			adminform=adminForm,
			is_popup=False,
			show_save_and_continue=False,
			media=media,
			inline_admin_formsets=inline_formsets,
			errors=helpers.AdminErrorList(form, formsets),
			preserved_filters=self.get_preserved_filters(request),
		)
		return self.render_change_form(request, context, add=True, change=False, obj=None)

@admin.register(SchoolYear)
class SchoolYearAdmin(admin.ModelAdmin):
	"""Creates admin interface for maintaining school years.
	"""
	list_display = ('start', 'end', 'isCurrent')

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
	"""Creates admin interface for maintaining teachers."""
	list_display = ('id', 'get_full_name', 'code')

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
	"""Creates admin interface for maintaining subjects."""
	list_display = ('id', 'fullname', 'code')

@admin.register(Division)
class DivisionAdmin(admin.ModelAdmin):
	"""Creates admin interface for maintaining divisions."""
	list_display = ('id', 'name', 'code')

@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
	"""Creates admin interface for maintaining classes."""
	list_display = ('id', 'code', 'getDivision')

