# -*- coding: utf-8 -*-
# vim: fenc=utf-8:ts=8:sw=8:si:sta:noet
from django.conf.urls import url
from . import views

urlpatterns = [
	url(r'^$', views.index, name='index'),
]
