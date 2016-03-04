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

from django.shortcuts import render
from django.http import HttpResponse
from standin.models import Plan, PlanEntry

def pupil(request):
	plan = Plan.objects.latest()
	if plan is not None:
		pupilPlan = plan.getPupilPlan()
	else:
		pupilPlan = []
	context = {
		'plan': plan,
		'planEntries': pupilPlan,
	}
	return HttpResponse(render(request, 'standin/pupil.html', context))

def teacher(request):
	context = {}
	return HttpResponse(render(request, 'standin/teacher.html', context))

