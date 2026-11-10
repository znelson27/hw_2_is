"""
views.py — HTTP request handlers for AttendanceChimp.

Each view corresponds to one URL endpoint.  Views receive an HTTP request,
interact with the database via models.py, and return an HTTP response.
"""

from django.shortcuts import render, redirect
from django.http import (HttpResponse, HttpResponseForbidden,
                         HttpResponseBadRequest, JsonResponse)
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from datetime import datetime
import zoneinfo
import json
import io
import random, string

from .models import (InstructorProfile, StudentProfile, CourseProfile, Lecture, QRCodeUpload)
#                    is_instructor, is_student,
#                    getUploadsForCourse

CDT = zoneinfo.ZoneInfo("America/Chicago")


# ---------------------------------------------------------------------------
# HW2  — index, time, sum
# ---------------------------------------------------------------------------

from datetime import datetime, date
from zoneinfo import ZoneInfo
from django.http import HttpResponse, JsonResponse

def index(request):
    """Render the home page (index.html)."""
    now = datetime.now(ZoneInfo("America/Chicago"))
    context = {'current_time':now.strftime("%H:%M"),'username':request.user.username}
    return render(request, 'app/index.html', context)

def time_view(request):
    """Return the current Central time formatted as 'HH:MM'in plain text."""
    now = datetime.now(ZoneInfo("America/Chicago"))
    return HttpResponse(now.strftime("%H:%M"), content_type="text/plain")

def sum_view(request):
   """Read query parameters n1 and n2 from GET request, convert them into a sum, and return JSON."""
   n1 = float(request.GET.get("n1"))
   n2 = float(request.GET.get("n2"))
   sum_string = n1+n2
   return HttpResponse(f"<p>{sum_string}<p>")


# ---------------------------------------------------------------------------
# HW4  — user creation
# ---------------------------------------------------------------------------

from django.views.decorators.http import require_GET, require_POST
from django.db import IntegrityError

@require_GET
def new(request):
    """ ONLY accepts get requests, renders new.html. """
    return render(request, 'app/new.html')

@csrf_exempt # otherwise raises csrf error
@require_POST
def createUser(request):
   """ ONLY accepts post requests, creates user profile & signup. """
   email = request.POST.get('email')
   user_name = request.POST.get('user_name')
   password = request.POST.get('password')
   is_student = request.POST.get('is_student')

   student = (is_student == 'true' or is_student == '1') # else does not know which profile to create

   if User.objects.filter(email=email).exists():
      return HttpResponseBadRequest("Email already taken")

   user = User.objects.create_user(username=user_name, email=email, password=password)

   profile_id = str(user.pk) # need unique user id
   if student:
      StudentProfile.objects.create(user=user, student_id=profile_id)
   else:
      InstructorProfile.objects.create(user=user, instructor_id=profile_id)

   login(request, user)
   return HttpResponse("Account created!")

# ---------------------------------------------------------------------------
# HW5  — courses, lectures, QR uploads, dump
# ---------------------------------------------------------------------------

@require_GET
def new_course(request):
   """ ONLY accepts get requests, renders new_course.html. """
   return render(request, 'app/new_course.html')

@require_GET
def new_lecture(request):
   """ ONLY accepts get requests, renders new_lecture.html. """
   return render(request, 'app/new_lecture.html')

@require_GET
def new_qr_upload(request):
   """ ONLY accepts get requests, renders new_qr_upload.html. """
   return render(request, 'app/new_qr_upload.html')

@csrf_exempt
@require_POST
def createCourse(request):
   """ Creates and saves course. Instructor gets HTTP 200; all others get 401."""
   instructor = request.user.is_authenticated and InstructorProfile.objects.filter(user=request.user).exists()

   if instructor:
      class_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
      CourseProfile.objects.create( 
         course_id=class_id, # need unique course id
         name=request.POST.get('course-name'),
         instructor=request.user.instructorprofile,
         start_time=request.POST.get('start-time'),
         end_time=request.POST.get('end-time'),
         day_mon='day-mon' in request.POST,
         day_tue='day-tue' in request.POST,
         day_wed='day-wed' in request.POST,
         day_thu='day-thu' in request.POST,
         day_fri='day-fri' in request.POST,
      )
      return HttpResponse("Course created!", status=200)
   else:
      return HttpResponse("Only instructors can create a course.", status=401)


@csrf_exempt
@require_POST
def createLecture(request):
   """ Creates and saves lecture. Instructor gets HTTP 200; all others get 401. Linked to Course."""
   instructor = request.user.is_authenticated and InstructorProfile.objects.filter(user=request.user).exists()

   if instructor:
      try:
         course = CourseProfile.objects.get(name=request.POST.get('choice'))
      except CourseProfile.DoesNotExist:
         return HttpResponseBadRequest("No such course") # must be linked to a course

      lect_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
      Lecture.objects.create(
         lecture_id=lect_id,
         course=course,
         date=date.today(),
         qr_code=''.join(random.choices(string.ascii_uppercase + string.digits, k=10)), #random
      )
      return HttpResponse("Lecture created!", status=200)
   else:
      return HttpResponse("Only instructors can create a lecture.", status=401)


@csrf_exempt
@require_POST
def createQRCodeUpload(request):
   """ Creates and saves QR code upload. Must be student, else 401."""
   student = request.user.is_authenticated and StudentProfile.objects.filter(user=request.user).exists()

   if student:
      imageUpload = request.FILES.get('imageUpload')
      if imageUpload is None:
         return HttpResponseBadRequest("No file uploaded") # account for possible errors

      QRCodeUpload.objects.create(
         student=request.user.studentprofile,
         image=imageUpload,
      )
      return HttpResponse("QR Code Uploaded!", status=200)
   else:
      return HttpResponse("Only students can upload a QR code.", status=401)


@csrf_exempt
@require_GET
def dumpUploads(request):
   """ Accepts GET requests, returns a JSON list with usernames/upload-times. Must be instructor. """
   instructor = request.user.is_authenticated and InstructorProfile.objects.filter(user=request.user).exists()
   
   if instructor:
      upload_list=[]
      for upload in QRCodeUpload.objects.all():
         upload_list.append({"username": upload.student.user.username, # "student" field in qr table
                             "upload_time": upload.uploaded_at.strftime("%Y-%m-%d %H:%M:%S"),
         })
      return JsonResponse(upload_list, safe=False)
   else:
      return HttpResponse("Only instructors can view QR uploads.", status=401)

# ---------------------------------------------------------------------------
# HW6  — getUploads
# ---------------------------------------------------------------------------



