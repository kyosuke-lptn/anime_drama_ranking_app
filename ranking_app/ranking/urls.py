from django.urls import path

from . import views

app_name = 'ranking'
urlpatterns = [
    path('', views.index, name='index'),
    path('category/<int:category_id>/', views.category, name='category'),
    path('detail/', views.show, name='show')
]
