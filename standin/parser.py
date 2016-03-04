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

from django.conf import settings
from standin import settings as app_settings
from standin.models import Teacher, Subject, SchoolYear, Division, Course, Plan, PlanEntry, Grade
from datetime import datetime
import django.dispatch
import json, pytz, re

# Define signals
plan_parsed = django.dispatch.Signal(providing_args=[])

class PlanParseException(Exception):
	"""Populated if a standin plan could not be parsed."""
	pass

class BaseParser:
	"""Base class to parse a standin plan of a third party app."""

	def __init__(self):
		pass

	def parse(self):
		pass

	def finished(self):
		plan_parsed.send(sender=self.__class__)

class DavinciJsonParser(BaseParser):
	"""Parser to parse a DaVinci export in JSON format."""

	def __init__(self, fileobj):
		super().__init__()

		self._jsonfile = fileobj

		# Get the current school year. If nothing is defined,
		# we do not need to process the file!
		self.schoolYear = None
		try:
			self.schoolYear = SchoolYear.getCurrentYear()
		except:
			raise PlanParseException('No matching school year defined!') 

	def parse(self):
		"""Parses the davinci json file!"""
		# load the file
		planContent = self._jsonfile.read()

		if planContent is None:
			raise PlanParseException('File not readable.')

		# get the encoding from settings (default: utf-8) and decode it.
		try:
			planContent = json.loads(planContent.decode(app_settings.get(app_settings.PLAN_FILES_ENCODING)))
		except ValueError:
			# in case of UTF-8, we try also the sig variant.
			if app_settings.get(app_settings.PLAN_FILES_ENCODING) == 'utf-8':
				planContent = json.loads(planContent.decode('utf-8-sig'))
			else:
				raise

		# parse file.
		self.parseTeachers(planContent['result'])
		self.parseSubjects(planContent['result'])
		self.parseDivisions(planContent['result'])
		self.parseCourses(planContent['result'])
		self.parseClasses(planContent['result'])
		self.parseTimeFrames(planContent['result'])

		# Get the version of the file, in order to create the plan header.
		version = planContent['about']['serverTimeStamp']
		version = datetime.strptime(version, '%Y%m%d %H%M')
		if settings.USE_TZ:
			version = version.replace(tzinfo=pytz.timezone(settings.TIME_ZONE))
		self.plan = Plan(vpstand=version)

		# Get each change.
		self.plan.save()
		changes = []
		for les in planContent['result']['displaySchedule']['lessonTimes']:
			# ignore entries without changes.
			# maybe they're later more interesting to auto-learn all courses,
			# not only those with changes.
			if 'changes' not in les.keys():
				continue

			result = self.parseChange(les)
			changes.extend(result)
			del(result)

		# no error occured? Nice. Activate the plan!
		for r in changes:
			r.save()
		self.plan.activate()

		self.finished()

	def parseChange(self, les):
		"""Parses one change entry (can produce multiple records)."""
		# they have different dates, depending on when the changes do apply.
		entryDates = []
		vptype = 0
		for dt in les['dates']:
			entryDates.append(datetime.strptime(dt, '%Y%m%d').date())

		# start and end time
		startTime = datetime.strptime(les['startTime'], '%H%M').time()
		endTime = datetime.strptime(les['endTime'], '%H%M').time()

		# to get the hours, we look into our timetable.
		if les['startTime'] in self.timeframes.keys():
			hour = self.timeframes[les['startTime']]
		else:
			hour = None

		# Get the teacher
		teacher = None
		for t in les['teacherCodes']:
			teacher = Teacher.objects.get(code=t)
			break
		if teacher is None:
			raise PlanParseException('No teacher given with reference %s' % (les['lessonRef'],))

		# Now as we have the teacher, we can update the course if necessary.
		course = Course.objects.get(id=les['courseRef'])
		if course.teacher is None:
			course.teacher = teacher
			course.save()

		# Get the affected classes
		classes = []
		for cl in les['classCodes']:
			classes.append(cl)

		# Rooms
		room = None
		if 'roomCodes' not in les.keys() or len(les['roomCodes']) <= 0:
			raise PlanParseException('No room given with reference %s' % (les['lessonRef'],))
		for r in les['roomCodes']:
			room = r
			break
		# Sometimes, the original given room contains already the new room, we don't want this; we need the original one!
		if 'absentRoomCodes' in les['changes'].keys():
			for r in les['changes']['absentRoomCodes']:
				room = r
				break

		# Details about the changes.
		# The supply subject is?
		chgSubject = None
		if 'newSubjectCode' in les['changes'].keys():
			chgSubject = Subject.objects.get(code=les['changes']['newSubjectCode'])
			vptype = vptype | PlanEntry.vptype.SUBJECT

		# Supply teacher (yes, DaVinci assumes, that there are multiple teachers - in theory not wrong).
		chgTeacher = None
		if 'newTeacherCodes' in les['changes'].keys():
			for t in les['changes']['newTeacherCodes']:
				chgTeacher = Teacher.objects.get(code=t)
				vptype = vptype | PlanEntry.vptype.TEACHER
				break

		# New room (no idea, how a course can be in different rooms...)?
		chgRoom = None
		if 'newRoomCodes' in les['changes'].keys():
			for t in les['changes']['newRoomCodes']:
				chgRoom = t
				vptype = vptype | PlanEntry.vptype.ROOM
				break

		# Possibility is, that the class will be absent.
		if 'reasonType' in les['changes'].keys() and les['changes']['reasonType'] == 'classAbsence':
			vptype = vptype | PlanEntry.vptype.CANCELLED

		# Or that the hour was moved or cancelled.
		chgDate = None
		chgHour = None
		chgTimeStart = None
		chgTimeEnd = None
		note = None
		if 'cancelled' in les['changes'].keys():
			if les['changes']['cancelled'] == 'movedAway':
				# possibility 1: just moved.
				vptype = vptype | PlanEntry.vptype.MOVED_TO
				# FIXME: lets extract the details.
				if 'caption' in les['changes'].keys():
					regex_moved_to = app_settings.get(app_settings.PLAN_PARSER_REGEX_MOVED_TO)
					if regex_moved_to is not None:
						matchMove = re.compile(regex_moved_to)
						r = matchMove.match(les['changes']['caption'])
						if r is not None:
							now = datetime(
								entryDates[0].year,
								entryDates[0].month,
								entryDates[0].day,
								startTime.hour,
								startTime.minute
							)
							startHour = r.group('startHour')
							for k,f in self.timeframes.items():
								if f == int(startHour):
									startHour = datetime.strptime(k, '%H%M').time()
									break
							if not hasattr(startHour, 'hour'):
								startHour = datetime.now().time()
							future = datetime(
								now.year,
								int(r.group('month')),
								int(r.group('day')),
								startHour.hour,
								startHour.minute
							)
							# if the future is already the past, we have to exchange:
							if future < now:
								past = future
								future = past.replace(year=past.year + 1)
							else:
								past = future.replace(year=future.year - 1)
							# depending on whats close to original date, we use that.
							if (future - now) <= (now - past):
								chgDate = future
							else:
								chgDate = past
							# the hour
							chgHour = int(r.group('startHour'))
							# now the times. ==> skipped @ FIXME!
			elif les['changes']['cancelled'] == 'classFree' or les['changes']['cancelled'] == 'lessonCancelled':
				# possibility 2: cancelled.
				vptype = vptype | PlanEntry.vptype.FREE

		# This entry could also be the inverse one to the above one (we need to parse the info field).
		if 'caption' in les['changes'].keys() and (vptype & PlanEntry.vptype.FREE) != PlanEntry.vptype.FREE \
			and (vptype & PlanEntry.vptype.MOVED_TO) != PlanEntry.vptype.MOVED_TO:
			regex_moved_from = app_settings.get(app_settings.PLAN_PARSER_REGEX_MOVED_FROM)
			if regex_moved_from is not None:
				matchMove = re.compile(regex_moved_from)
				r = matchMove.match(les['changes']['caption'])
				if r is not None:
					vptype = vptype | PlanEntry.vptype.MOVED_FROM
					now = datetime(
						entryDates[0].year,
						entryDates[0].month,
						entryDates[0].day,
						startTime.hour,
						startTime.minute
					)
					startHour = r.group('startHour')
					for k,f in self.timeframes.items():
						if f == int(startHour):
							startHour = datetime.strptime(k, '%H%M').time()
							break
					if not hasattr(startHour, 'hour'):
						startHour = datetime.now().time()
					future = datetime(
						now.year,
						int(r.group('month')),
						int(r.group('day')),
						startHour.hour,
						startHour.minute
					)
					# if the future is already the past, we have to exchange:
					if future < now:
						past = future
						future = past.replace(year=past.year + 1)
					else:
						past = future.replace(year=future.year - 1)
					# depending on whats close to original date, we use that.
					if (future - now) <= (now - past):
						chgDate = future
					else:
						chgDate = past
					# the hour
					chgHour = int(r.group('startHour'))
					# now the times. ==> skipped @ FIXME!
		# some notes?
		if 'information' in les['changes']:
			note = les['changes']['information']

		# finally create the records (for every day!)
		records = []
		for grade in classes:
			gradeObj = Grade.objects.get(code=grade)
			for day in entryDates:
				p = PlanEntry(
					header=self.plan,
					day=day,
					hour=hour,
					timeStart=startTime,
					timeEnd=endTime,
					grade=gradeObj,
					course=course,
					room=room,
					supplyTeacher=chgTeacher,
					supplySubject=chgSubject,
					supplyRoom=chgRoom,
					supplyDate=chgDate,
					supplyHour=chgHour,
					supplyTimeStart=chgTimeStart,
					supplyTimeEnd=chgTimeEnd,
					note=note,
					vptype=vptype
				)
				records.append(p)

		return records

	def parseTeachers(self, planContent):
		"""Parses all teachers"""
		# load the teacher first (to have a proper connection).
		for tf in planContent['teachers']:
			t = Teacher.objects.get_or_create(id=tf['id'], code=tf['code'])
			t = t[0]
			t.first_name = tf['firstName'] if 'firstName' in tf else None
			t.last_name = tf['lastName'] if 'lastName' in tf else None
			t.save()

	def parseSubjects(self, planContent):
		"""Parses all subjects from file"""
		# All subjects
		for tf in planContent['subjects']:
			Subject.objects.get_or_create(id=tf['id'], code=tf['code'], fullname=tf['description'] if 'description' in tf else tf['code'])

	def parseDivisions(self, planContent):
		"""Parses all divisions from file"""
		# All divisions
		for tf in planContent['teams']:
			Division.objects.get_or_create(
				id=tf['id'], code=tf['code'], name=tf['description'] if 'description' in tf else tf['code']
			)

	def parseCourses(self, planContent):
		"""Parses all courses from file"""
		# All courses (teacher must be learned later).
		for tf in planContent['courses']:
			# first get the subject.
			subject = Subject.objects.get(id=tf['subjectRef'])
			Course.objects.get_or_create(
				id=tf['id'], schoolYear=self.schoolYear, subject=subject, name=tf['title']
			)

	def parseClasses(self, planContent):
		"""Parses all classes from file"""
		# All classes
		for tf in planContent['classes']:
			# find the division!
			div = None
			if 'teamRefs' in tf.keys():
				for cl in tf['teamRefs']:
					div = Division.objects.get(id=cl)
					if div is not None:
						break
			Grade.objects.get_or_create(
				id=tf['id'], code=tf['code'], division=div, schoolYear=self.schoolYear
			)

	def parseTimeFrames(self, planContent):
		"""Parses timetable from file"""
		# For the DaVinci plan, we first need to get the timetable in order to populate the 
		# "hours" correctly.
		self.timeframes = {}
		for tf in planContent['timeframes']:
			# but only the standard one, not the duty one.
			if tf['code'] == 'Standard':
				for t in tf['timeslots']:
					self.timeframes[t['startTime']] = int(t['label'])

