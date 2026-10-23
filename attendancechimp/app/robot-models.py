"""
robot-models.py -- LLM-generated data model for attendancechimp

LLM used: Claude (Claude Sonnet 5.5, Anthropic)

Prompt given to the LLM:
    "Generate a Django models.py for AttendanceChimp, an app that tracks class
    attendance via QR codes. Requirements: users are students and instructors
    (use separate InstructorProfile and StudentProfile tables). Each course has one instructor and a
    meeting schedule; students can enroll in many courses (Enrollment junction table).
    Lectures belong to a course and have a date and a QR identifier. QRCodeUpload
    holds photos uploaded by students, linked to a student and optionally a
    lecture. The design should be simple to use, support attendance analytics,
    and be robust to cheating. Write a detailed docstring for each model and
    include helper functions where useful."

Note: the file name contains a hyphen, so Python cannot import it as a module.
That is intentional -- it is a reference file for comparison, not part of the
live app. Django will not pick it up for migrations.

ImageField requires Pillow (pip install pillow) if this is ever used live.
"""

import hashlib
import secrets

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


def generate_qr_token():
    """Return a URL-safe random token used as a lecture's QR identifier.

    Random (not sequential) so a student cannot guess the code for a lecture
    they did not attend.
    """
    return secrets.token_urlsafe(16)


class InstructorProfile(models.Model):
    """Extra data for a user who teaches courses.

    Separate from StudentProfile because instructors and students have
    different attributes and permissions (instructors create courses and
    lectures; students upload QR photos). Splitting the roles also lets the
    database enforce that Course.instructor can only point at an instructor,
    which a single Users table with a 'role' column could not do.

    Fields:
        user: one-to-one link to Django's built-in User (handles login/password).
        department: optional department name.
    """

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="instructor_profile"
    )
    department = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Instructor: {self.user.get_full_name() or self.user.username}"


class StudentProfile(models.Model):
    """Extra data for a user who attends courses.

    Fields:
        user: one-to-one link to Django's built-in User.
        student_id: institutional ID, unique so one person cannot hold two
            student records.
    """

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="student_profile"
    )
    student_id = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return f"Student: {self.user.get_full_name() or self.user.username}"


class Course(models.Model):
    """A course taught by exactly one instructor.

    The meeting schedule is stored as a weekday list plus start/end times
    (e.g. "MWF", 10:30-11:20), which is enough for display and for checking
    whether an upload time falls within a plausible class window.

    Fields:
        name: human-readable title.
        code: short course code, e.g. "DATA 13600".
        instructor: the teaching instructor. PROTECT prevents deleting an
            instructor who still has courses (avoids silently losing
            attendance history).
        meeting_days: weekday letters, e.g. "MWF" or "TR".
        start_time, end_time: daily meeting window.
        term: e.g. "Autumn 2026".
        students: many-to-many to StudentProfile through Enrollment.
    """

    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20)
    instructor = models.ForeignKey(
        InstructorProfile, on_delete=models.PROTECT, related_name="courses"
    )
    meeting_days = models.CharField(max_length=10, help_text='e.g. "MWF" or "TR"')
    start_time = models.TimeField()
    end_time = models.TimeField()
    term = models.CharField(max_length=30)
    students = models.ManyToManyField(
        StudentProfile, through="Enrollment", related_name="courses"
    )

    class Meta:
        unique_together = ("code", "term")

    def __str__(self):
        return f"{self.code}: {self.name} ({self.term})"


class Enrollment(models.Model):
    """Join table linking a student to a course (many-to-many).

    Stored as an explicit model so it can carry its own data (when the student
    enrolled, whether the enrollment is still active) and so analytics can
    query "who is supposed to be in this course" directly.

    The (student, course) pair is unique: a student cannot enroll twice.
    """

    student = models.ForeignKey(
        StudentProfile, on_delete=models.CASCADE, related_name="enrollments"
    )
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="enrollments"
    )
    enrolled_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("student", "course")

    def __str__(self):
        return f"{self.student} in {self.course}"


class Lecture(models.Model):
    """One class meeting of a course.

    Each lecture has its own random QR token. The instructor displays a QR
    code encoding this token in class; students photograph it. Because the
    token differs for every lecture, a photo from a previous session cannot
    be reused to claim attendance.

    Fields:
        course: the course this meeting belongs to.
        date: calendar date of the meeting.
        qr_identifier: unique random token encoded in the displayed QR code.
        opens_at / closes_at: optional window during which uploads are
            accepted; uploads outside it can be flagged as suspicious.
    """

    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="lectures"
    )
    date = models.DateField()
    qr_identifier = models.CharField(
        max_length=64, unique=True, default=generate_qr_token, editable=False
    )
    opens_at = models.DateTimeField(null=True, blank=True)
    closes_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("course", "date")
        ordering = ["course", "date"]

    def is_open(self, when=None):
        """Return True if uploads are currently accepted for this lecture.

        If no window is set, the lecture is treated as always open.
        """
        when = when or timezone.now()
        if self.opens_at and when < self.opens_at:
            return False
        if self.closes_at and when > self.closes_at:
            return False
        return True

    def __str__(self):
        return f"{self.course.code} on {self.date}"


class QRCodeUpload(models.Model):
    """A photo of a lecture's QR code uploaded by a student.

    The lecture is optional (null=True) because the upload is created before
    the QR code has been decoded and matched to a lecture. Once decoded, the
    lecture is filled in and the upload can be validated.

    Anti-cheating fields:
        uploaded_at: set by the server, never by the client, so timestamps
            cannot be forged.
        image_hash: SHA-256 of the image bytes. A repeated hash across
            different students suggests one photo was shared.
        decoded_value: the text read from the QR code; compared against
            Lecture.qr_identifier to confirm it is the right lecture.
        is_valid: True only if the decoded value matches the lecture AND the
            student is enrolled AND the lecture was open at upload time.

    Constraint: at most one valid upload per (student, lecture), so a student
    is counted present once.
    """

    student = models.ForeignKey(
        StudentProfile, on_delete=models.CASCADE, related_name="uploads"
    )
    lecture = models.ForeignKey(
        Lecture,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploads",
    )
    image = models.ImageField(upload_to="qr_uploads/%Y/%m/%d/")
    image_hash = models.CharField(max_length=64, blank=True, db_index=True)
    decoded_value = models.CharField(max_length=64, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_valid = models.BooleanField(default=False)

    class Meta:
        ordering = ["-uploaded_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "lecture"],
                condition=models.Q(is_valid=True),
                name="one_valid_upload_per_student_per_lecture",
            )
        ]

    def compute_image_hash(self):
        """Return the SHA-256 hex digest of the uploaded image's bytes."""
        hasher = hashlib.sha256()
        self.image.open("rb")
        for chunk in self.image.chunks():
            hasher.update(chunk)
        self.image.close()
        return hasher.hexdigest()

    def validate(self):
        """Set is_valid based on enrollment, QR match, and the upload window.

        Call after decoded_value and lecture have been set. Does not save.
        """
        if self.lecture is None:
            self.is_valid = False
            return
        enrolled = Enrollment.objects.filter(
            student=self.student, course=self.lecture.course, is_active=True
        ).exists()
        matches = self.decoded_value == self.lecture.qr_identifier
        self.is_valid = enrolled and matches and self.lecture.is_open(
            self.uploaded_at or timezone.now()
        )

    def __str__(self):
        return f"{self.student} upload for {self.lecture} ({'valid' if self.is_valid else 'unverified'})"
