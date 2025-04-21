# from django.contrib import admin
from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('', views.index, name='index'),
    path('yt_menu/', views.yt_menu, name='yt_menu'),
    path('upload/', views.upload_file, name='upload_file'),
    path('drag_n_drop_menu/', views.drag_n_drop_menu, name='drag_n_drop_menu'),
    path('drag_n_drop_menu/download', views.drag_n_drop_menu_download, name='drag_n_drop_menu_download'),
    path('<str:file_name>/', views.download_file, name='drag_n_drop_menu_download'),
    path('yt_menu/download/', views.yt_menu_download, name='yt_menu_download'),
    path('<str:file_name>/', views.download_file, name='yt_menu_download'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
