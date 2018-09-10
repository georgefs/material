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
from django.contrib.auth.decorators import login_required

urlpatterns = [
    re_path('video/(?P<vid>\d+).m3u8', views.video_m3u8, name="video_m3u8"),
    re_path('scene/(?P<vid>\d+).m3u8', views.scene_m3u8, name="scene_m3u8"),
    re_path('video/(?P<vid>\d+)/preview', views.video_preview, name="video_preview"),
    re_path('video/(?P<vid>\d+)/slice', login_required(views.VideoSlinceView.as_view()), name="video_slice"),
    re_path('scene/(?P<vid>\d+)/edit', login_required(views.SceneEditorView.as_view()), name="scene_edit"),
    re_path('scene/(?P<vid>\d+)/preview', views.scene_preview, name="scene_preview"),
    re_path('video/streaming/(?P<vid>\d+).m3u8', views.video_streaming_m3u8, name="video_streaming_m3u8"),
]
