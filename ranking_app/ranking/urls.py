from django.urls import path

from . import views

app_name = 'ranking'
urlpatterns = [
    path('', views.index, name='index'),
    path('animations/', views.animation, name = 'animation'),
    path('dramas/', views.drama, name = 'drama'),
    path('detail/', views.show, name = 'show')
]
