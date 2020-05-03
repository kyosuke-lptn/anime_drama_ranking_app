from django.urls import path

from . import views

app_name = 'ranking'
urlpatterns = [
    path('', views.index, name='index'),
    path('category/<int:category_id>/', views.category_index, name='category'),
    path('content/<int:content_id>', views.content_detail,
         name='content_detail'),
    path('content/<int:content_id>/rank_graph', views.get_svg,
         name='content_rank_graph'),
]
