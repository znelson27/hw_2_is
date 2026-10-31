from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('time/', views.time_view, name='current_time'),
    path('sum/', views.sum_view, name='sum'),
    path('index.html', views.index, name='index_html'),
    path('new', views.new, name='new_signup_page'),
    path('createUser', views.createUser, name='create_user')
]
