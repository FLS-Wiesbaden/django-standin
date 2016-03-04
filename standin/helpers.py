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
import copy

class PlanDay:

	def __init__(self, day):
		self.day = day
		self._grades = []

	def addEntry(self, entry):
		found = False
		for g in self._grades:
			if g.grade == entry.grade:
				g.addEntry(entry)
				found = True
				break

		if found is False:
			grade = PlanGrade(entry.grade)
			grade.addEntry(entry)
			self._grades.append(grade)

	def __iter__(self):
		for d in self._grades:
			yield d

class PlanGrade:

	def __init__(self, grade):
		self.grade = grade
		self._entries = []

	def addEntry(self, entry):
		self._entries.append(entry)

	def __iter__(self):
		for d in self._entries:
			yield d

class PlanIterer:
	"""Class to easily iterate in views."""

	def __init__(self):
		self._days = []

	def addEntry(self, entry):
		day = self.findDay(entry.day)
		if day is not None:
			day.addEntry(entry)

	def findDay(self, entryDay):
		for d in self._days:
			if d.day == entryDay:
				return d
		return None

	def addDay(self, day):
		self._days.append(PlanDay(day))

	def __iter__(self):
		for d in self._days:
			yield d

class PlanEntryGroup:
	"""This class groups multiple entries which are similiar to each other and where
	e.g. only the hour / start or end time is different."""

	def __init__(self, base):
		self._base = base

	@classmethod
	def createGroup(group, entry, nextEntry):
		group = PlanEntryGroup(entry)
		for attr in entry.__dict__:
			if attr not in ['id', 'hour', 'timeStart', 'timeEnd']:
				setattr(group, attr, getattr(entry, attr))
		group._entries = [entry, nextEntry]
		return group

	def __getattr__(self, name):
		# for hours, we return always the highest!
		if name == 'hour':
			return self.maxHour()

		if hasattr(self._base, name):
			return getattr(self._base, name)
		else:
			return None

	def add(self, entry):
		self._entries.append(entry)

	def maxHour(self):
		hours = [e.hour for e in self._entries]
		return max(hours)

	def getHour(self):
		# min number.
		hours = [e.hour for e in self._entries]
		return '%d.-%d.' % (min(hours), max(hours))

	def getSupplyHour(self):
		# min number.
		hours = [e.supplyHour for e in self._entries]
		return '%d.-%d.' % (min(hours), max(hours))

	def is_group(self):
		return True

	def similiar(self, entry):
		# pick always the last entry!
		return self._entries[len(self._entries) - 1].similiar(entry)

