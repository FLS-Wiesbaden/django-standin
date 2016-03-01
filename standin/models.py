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

from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
import pytz, datetime, uuid

class Teacher(models.Model):
	"""A teacher in school.

	This class represents a teacher in a school. The teacher can be ill or he can 
	jump in for a colleague.

	Basically, later a teacher should be able to be connected to a single user - e.g. by
	the shortcut / "nickname", used often in e.g. DaVinci.
	"""

	class Meta:
		verbose_name = _('Teacher')

	# we identify it through a UUID (as we get e.g. from DaVinci)
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

	# independent of which auth user model is used, it will definitly
	# have a field "teacher".
	user = models.OneToOneField(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		null=True
	)
	# the teacher must have a "nickname"
	code = models.CharField(max_length=120, unique=True, null=True)

	def get_full_name(self):
		if self.user is None:
			return ''
		else:
			return self.user.get_full_name()
	get_full_name.short_description = _('Full name')

class Subject(models.Model):
	"""Describes a subject
	
	It seems strange, but this class represents a subject. There cannot be so much 
	different attributes, to have a reason to split. Obviously, the software
	was written in Germany. There are many schools which are afraid of data misuse. 
	So for data privacy, it could be, that we should show only a "nickname", a "abbrevation".
	"""

	class Meta:
		verbose_name = _('Subject')

	# we identify it through a UUID (as we get e.g. from DaVinci)
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

	# beside of a course, the subject is independent of the school year, because
	# the attributes cannot change!
	fullname = models.CharField(max_length=80)
	code = models.CharField(max_length=20, unique=True)

class SchoolYear(models.Model):
	"""A year of a school

	Every school has a recurring year. In Germany it is the same for all schools, 
	it is from summer holiday to summer holiday. So the date itself is varying for each
	province and each year. We'll take care here.
	"""

	class Meta:
		verbose_name = _('School year')

	start = models.DateField()
	end = models.DateField()

	def isCurrent(self):
		"""Checks if this school year is the current one."""
		now = datetime.date.today()
		return now >= self.start and now <= self.end
	isCurrent.boolean = True
	isCurrent.short_description = 'Current school year'

	def __str__(self):
		"""Returns representation of a school year"""
		return '%s - %s' % (
			self.start.strftime('%x'),
			self.end.strftime('%x')
		)

	@staticmethod
	def getCurrentYear():
		"""Gets the school year which is currently active!"""
		now = datetime.date.today()
		return SchoolYear.objects.get(start__lte=now, end__gte=now)

class Division(models.Model):
	"""Different divisions ("School Type") in a school.

	A school can have different "divisions" in a school:
		- vocational [business] school
		- secondary school
		- HBFS
		- HBFSI
	"""

	class Meta:
		verbose_name = _('Type of school')

	# we identify it through a UUID (as we get e.g. from DaVinci)
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

	name = models.CharField(max_length=50, unique=True)
	code = models.CharField(max_length=20, null=True)
	# FIXME: maybe regexp in order to recognize it?

	def __str__(self):
		"""Returns representation of a division"""
		if self.code is not None:
			return '%s (%s)' % (self.name, self.code)
		else:
			return self.name

class Course(models.Model):
	"""A course at a specific time for a specific group

	In the old implementation, we had a stupid plan. It was not able to "recognize" connections.
	A course has a description or name, subject, teacher - the room, etc. can change depending
	on the weekday and the time.
	Additionally a course can be for mixed classes! E.g. sports, religion.

	Important: the table can and will change every year!
	"""
	#FIXME: add validator when saving, that the schoolYear does not already exist!

	class Meta:
		verbose_name = _('Course')

	# we identify it through a UUID (as we get e.g. from DaVinci)
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

	schoolYear = models.ForeignKey(SchoolYear, verbose_name=_('School year'))
	teacher = models.ForeignKey(Teacher, null=True, verbose_name=_('Original teacher'))
	subject = models.ForeignKey(Subject, verbose_name=_('Original subject'))
	name = models.CharField(max_length=15, verbose_name=_('Course name'))

	# Sometimes we need to group it with a specific "name"
	# In order to know this, we must be able to define "rules" for this.
	groupBy = models.CharField(max_length=15, null=True, verbose_name=_('Class name'))

class Grade(models.Model):
	"""A class consists of multiple pupils and it has multiple courses."""

	class Meta:
		verbose_name = _('Class')
		verbose_name_plural = _('Classes')
		unique_together = ('schoolYear', 'code')

	# we identify it through a UUID (as we get e.g. from DaVinci)
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

	schoolYear = models.ForeignKey(SchoolYear, verbose_name=_('School year'))
	code = models.CharField(max_length=50, verbose_name=_('Class code'))
	division = models.ForeignKey(Division, null=True, verbose_name=_('Division'))
	courses = models.ManyToManyField(Course)

	def getDivision(self):
		"""Returns the division name (if allocated)."""
		if self.division is not None:
			return self.division.name
		else:
			return ''
	getDivision.short_description = _('Division')

class Plan(models.Model):
	"""The plan keeps main data about one plan!

	Each plan has multiple entries, see PlanEntries. A plan have some
	header informations like: when were the data extracted and when were
	the data uploaded. There is a big difference and this is important.
	The export date is mostly extracted out of the file and tells the "version"
	of the plan.
	"""

	class Meta:
		verbose_name = _('Standin plan')
		ordering = ['vpdtup']
	
	vpdtup = models.DateTimeField(auto_now_add=True, verbose_name=_('Upload date and time'))
	vpstand = models.DateTimeField(verbose_name=_('Date and time of data'))
	# we should consider only active, finished records (so we can create plans without breaking the 
	# the view)
	vpactive = models.BooleanField(default=False, verbose_name=_('Active'))
	
	def __str__(self):
		"""Returns representation of a plan"""
		return 'Plan of %s, uploaded on %s' % (
			self.vpstand.strftime('%x %H:%M:%S'),
			self.vpdtup.strftime('%x %H:%M:%S')
		)

	def activate(self):
		"""Activates the plan."""
		self.vpactive = True
		self.save()

class PlanEntry(models.Model):
	"""An entry of a plan.
	"""
	TYPE_UNKNOWN = 0
	TYPE_CANCELLED = 1
	TYPE_ROOM = 2
	TYPE_TEACHER = 4
	TYPE_SUBJECT = 8
	TYPE_DATETIME = 16
	TYPE_MOVED_FROM = 32
	TYPE_MOVED_TO = 64
	TYPE_FREE = 128
	TYPE_DUTY = 512

	class Meta:
		verbose_name = _('Standin')
	
	# An entry is always a part of a "plan". Add the reference here.
	header = models.ForeignKey(Plan, verbose_name=_('Plan header'))
	day = models.DateField(verbose_name=_('Day of standin'))
	# A normal class has different hours. But that could be irritating, as
	# there are also 0. hour or sometimes e.g. DaVinci can also provide schoolyard duties.
	# We want to be able to track both.
	hour = models.PositiveSmallIntegerField(verbose_name=_('Hour'))
	timeStart = models.TimeField()
	timeEnd = models.TimeField()
	# A standin consists always of: Class/Course, Subject, Teacher, Room,
	# and sometimes one or multiple of changed data:
	# changed teacher, changed subject, changed room
	# Yes: even different date and time.
	# For personal track, we should
	grade = models.ForeignKey(Grade, verbose_name=_('Affected class'))
	course = models.ForeignKey(Course, verbose_name=_('Affected course'))
	room = models.CharField(max_length=15, verbose_name=_('Original room'))
	# Supply data:
	supplyTeacher = models.ForeignKey(Teacher, null=True, verbose_name=_('Supply teacher'))
	supplySubject = models.ForeignKey(Subject, null=True, verbose_name=_('Supply teacher'))
	supplyRoom = models.CharField(max_length=15, null=True, verbose_name=_('Supply room'))
	# Moved to another date and time (this gives us total new possibilities)?
	supplyDate = models.DateField(null=True, verbose_name=_('Supply date'))
	supplyHour = models.PositiveSmallIntegerField(null=True, verbose_name=_('Supply hour'))
	supplyTimeStart = models.TimeField(null=True, verbose_name=_('Supply time start'))
	supplyTimeEnd = models.TimeField(null=True, verbose_name=_('Supply time end'))
	# general note (however, 550 characters is really big....)
	note = models.TextField(max_length=550, null=True, verbose_name=_('Information'))
	# Depending on the data, there are different types
	# (e.g. moved, free, normal standin, cancelled).
	vptype = models.PositiveSmallIntegerField(verbose_name=_('Type of standin'))
	
	def __str__(self):
		"""Returns representation of a plan entry"""
		return 'Plan entry on %s' % (
			self.day.strftime('%x'),
		)

