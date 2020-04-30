from django.urls import path

from . import views

app_name = 'ranking'
urlpatterns = [
    path('', views.index_view, name='index'),
    path('category/<int:category_id>/', views.category_view, name='category'),
    path('dramas/', views.drama, name='show'),
    path('detail/', views.show, name='show')
]
