from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('time/', views.time_view, name='current_time'),
    path('sum/', views.sum_view, name='sum'),
    path('index.html', views.index, name='index_html'),
    path('new', views.new, name='new_signup_page'),
    path('createUser', views.createUser, name='create_user'),
    path('new_course', views.new_course, name='new_course'),
    path('createCourse', views.createCourse, name='create_course'),
    path('new_lecture', views.new_lecture, name='new_lecture'),
    path('createLecture', views.createLecture, name='create_lecture'),
    path('new_qr_upload', views.new_qr_upload, name='new_qr_upload'),
    path('createQRCodeUpload', views.createQRCodeUpload, name='create_qr_upload'),
    path('dumpUploads', views.dumpUploads, name='dump_uploads'),
]
