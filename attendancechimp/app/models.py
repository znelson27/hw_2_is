"""
models.py — Data model for AttendanceChimp.

AttendanceChimp is an electronic class attendance tool.  Instructors create
courses and lectures; each lecture is assigned a random QR code.  Students
photograph the QR code and upload the image.  The system decodes the QR code,
matches it to a lecture, and records the attendance.

Entities
--------
- CourseProfile   : extends Django User → instructor-specific data
- StudentProfile  : extends Django User → student-specific data
- Course          : a course taught by one instructor
- Enrollment      : junction table linking students to courses
- Lecture         : a single class meeting (has a QR-code identifier)
- QRCodeUpload    : a student's uploaded QR-code photograph
"""

from django.db import models
from django.contrib.auth.models import User

import logging
import string
import random

logger = logging.getLogger(__name__) # set up tracking, auditing, and debugging
                                                               # allows using logger.warning(), logger.error(), 
                                                               # logger.info(), etc. Better than print() for debuggin... 


# ---------------------------------------------------------------------------
# User profiles
# ---------------------------------------------------------------------------

class StudentProfile(models.Model):
   """ 
   Record of students, including unique ID and first/last name.
   """
   student_id = models.CharField(max_length=8, primary_key=True)
   first_name = models.CharField(max_length=30)
   last_name = models.CharField(max_length=30)

class InstructorProfile(models.Model):
   """
   Record of instructors, including unique ID and first/last name. 
   """
   instructor_id = models.CharField(max_length=8, primary_key=True)
   first_name = models.CharField(max_length=30)
   last_name = models.CharField(max_length=30)


# ---------------------------------------------------------------------------
# Course
# ---------------------------------------------------------------------------

class CourseProfile(models.Model):
   """ 
   Record of courses, including unique ID, name, instructor, meeting schedule.
   Also creates many-to-many (junction) table "enrollment" linking students to courses.
   """
   course_id = models.CharField(max_length=4, primary_key=True)
   name = models.CharField()
   instructor = models.ForeignKey(InstructorProfile, on_delete=models.CASCADE)
   meeting_sched = models.DateTimeField()
   enrollment = models.ManyToManyField(StudentProfile)

# ---------------------------------------------------------------------------
# Enrollment
# ---------------------------------------------------------------------------

# see above
   

# ---------------------------------------------------------------------------
# Lecture
# ---------------------------------------------------------------------------

class Lecture(models.Model):
   """
   Record of lectures, including unique ID, course, date, and QR code identifier.
   """
   lecture_id = models.CharField(max_length=4, primary_key=True)
   course = models.ForeignKey(CourseProfile, on_delete=models.CASCADE)
   date = models.DateField()
   qr_code = models.CharField(max_length=10)


# ---------------------------------------------------------------------------
# QR Code Upload
# ---------------------------------------------------------------------------

class QRCodeUpload(models.Model):
   """
   Record of QR codes uploaded, including student and (optionally) lecture.
   """
   student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
   lecture = models.OneToOneField(Lecture, on_delete=models.PROTECT)


# ---------------------------------------------------------------------------
# Helper / API functions
# ---------------------------------------------------------------------------



