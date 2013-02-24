# coding: utf-8

from django.conf.urls import patterns, include, url
from django.contrib.auth.views import login
from django.contrib.auth.views import logout

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'diffapp.views.index', name='home'),
    url(r'^S(\d+)/$', 'diffapp.views.show_commit_sequence', name='commit_sequence'),
    url(r'^S(\d+)/new_comment$', 'diffapp.views.ajax_new_comment', name='ajax_new_comment'),
    url(r'^S(\d+)/save_comment$', 'diffapp.views.ajax_save_comment', name='ajax_save_comment'),
    url(r'^S(\d+)/del_comment$', 'diffapp.views.ajax_del_comment', name='ajax_del_comment'),

    # Аутентификация
    url(r'^login/$', login, name='login'),
    url(r'^logout/$', logout, {"next_page": "/"}, name='logout'),

    # url(r'^diffserver/', include('diffserver.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
