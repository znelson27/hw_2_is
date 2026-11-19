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
from django.utils import timezone

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
   Record of students, including unique ID and first/last name. Auth using Django's User model.
   """
   user = models.OneToOneField(User, on_delete=models.CASCADE)
   student_id = models.CharField(max_length=8, primary_key=True)
   first_name = models.CharField(max_length=30)
   last_name = models.CharField(max_length=30)

class InstructorProfile(models.Model):
   """
   Record of instructors, including unique ID and first/last name. Auth using Django's User model.
   """
   user = models.OneToOneField(User, on_delete=models.CASCADE)
   instructor_id = models.CharField(max_length=8, primary_key=True)
   first_name = models.CharField(max_length=30)
   last_name = models.CharField(max_length=30)

def is_instructor(user):
    return user.is_authenticated and InstructorProfile.objects.filter(user=user).exists()

def is_student(user):
    return user.is_authenticated and StudentProfile.objects.filter(user=user).exists()

# ---------------------------------------------------------------------------
# Course
# ---------------------------------------------------------------------------

class CourseProfile(models.Model):
   """ 
   Record of courses, including unique ID, name, instructor, meeting schedule.
   Also creates many-to-many (junction) table "enrollment" linking students to courses.
   """
   course_id = models.CharField(max_length=4, primary_key=True)
   name = models.CharField(max_length=100,unique=True)
   instructor = models.ForeignKey(InstructorProfile, on_delete=models.CASCADE)
   enrollment = models.ManyToManyField(StudentProfile)
   start_time = models.TimeField()
   end_time = models.TimeField()
   day_mon = models.BooleanField(default=False)
   day_tue = models.BooleanField(default=False)
   day_wed = models.BooleanField(default=False)
   day_thu = models.BooleanField(default=False)
   day_fri = models.BooleanField(default=False)

   # need function which encapsulates all boolean fields
   def meets_on_day(self, weekday): # course, day
    days = [self.day_mon, self.day_tue, self.day_wed, self.day_thu, self.day_fri] #list boolean vals
    return weekday < 5 and days[weekday] # no classes on sat/sun, but must handle uploads
    # will return false for weekends, and if true, will index weekday from days and return true/false
    # for that course.

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
   date = models.DateField(auto_now_add=True)
   qr_code = models.CharField(max_length=10)


# ---------------------------------------------------------------------------
# QR Code Upload
# ---------------------------------------------------------------------------

class QRCodeUpload(models.Model):
   """
   Record of QR codes uploaded, including student and (optionally) lecture.
   """
   student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
   lecture = models.ForeignKey(Lecture, on_delete=models.SET_NULL, null=True)
   image = models.ImageField(upload_to="qr_code_uploads/%Y/%m/%d/")
   uploaded_at = models.DateTimeField(auto_now_add=True) # timestamp to verify upload durng lecture


# ---------------------------------------------------------------------------
# Helper / API functions
# ---------------------------------------------------------------------------

def getUploadsForCourse(course):
   """
   Input= unique course code. Output= List of QRCodeUpload objects valid for that course.
   """
   
   valid_codes = [] # will append qr codes to this

   # fk chain: lecture.course must exist
   for lecture in Lecture.objects.filter(course=course): # all lectues belonging to course we called
      for upload in QRCodeUpload.objects.filter(lecture=lecture): # nested loop- codes for filt lec
         upload_time = timezone.localtime(upload.uploaded_at) # attribute from uploads table
         if (course.meets_on_day(upload_time.weekday()) and 
             course.start_time <= upload_time.time() <= course.end_time):
               valid_codes.append(upload)
   return valid_codes
