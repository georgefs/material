"""conf URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path
from . import views

urlpatterns = [
    re_path('video/(?P<vid>\d+).m3u8', views.video_m3u8, name="video_m3u8"),
    re_path('scene/(?P<vid>\d+).m3u8', views.scene_m3u8, name="scene_m3u8"),
    re_path('scene/(?P<vid>\d+)/preview_images', views.scene_preview_images, name="scene_preview_images"),
    re_path('video/(?P<vid>\d+)/preview', views.video_preview, name="video_preview"),
    re_path('scene/(?P<vid>\d+)/preview', views.scene_preview, name="scene_preview"),
]
