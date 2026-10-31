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

from .models import (InstructorProfile, StudentProfile, CourseProfile, Lecture, QRCodeUpload)
#                    is_instructor, is_student,
#                    getUploadsForCourse

CDT = zoneinfo.ZoneInfo("America/Chicago")


# ---------------------------------------------------------------------------
# HW2  — index, time, sum
# ---------------------------------------------------------------------------

from datetime import datetime
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



# ---------------------------------------------------------------------------
# HW6  — getUploads
# ---------------------------------------------------------------------------



