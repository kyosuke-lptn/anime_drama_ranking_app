from django.urls import path

from . import views

app_name = 'ranking'
urlpatterns = [
    path('', views.index, name='index'),
    path('category/', views.show1, name = 'show1'),
    path('detail/', views.show, name = 'show')
]
