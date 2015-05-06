# coding: utf-8

from django.conf import settings
from django.conf.urls import patterns, url
from django.contrib.auth.views import login, logout
from django.contrib.auth.views import password_change, password_change_done

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'diffapp.views.index', name='home'),
    url(r'^S(\d+)/$', 'diffapp.views.show_commit_sequence', name='commit_sequence'),
    url(r'^S(\d+)/new_comment$', 'diffapp.views.ajax_new_comment', name='ajax_new_comment'),
    url(r'^S(\d+)/save_comment$', 'diffapp.views.ajax_save_comment', name='ajax_save_comment'),
    url(r'^S(\d+)/del_comment$', 'diffapp.views.ajax_del_comment', name='ajax_del_comment'),
    url(r'^S(\d+)/exported-comments/$', 'diffapp.views.export_comments_redmine', name='export_comments'),
    url(r'^submit-diff-api/$', 'diffapp.views.submit_diff_api', name='submit-diff-api'),

    # Аутентификация
    url(r'^login/$', login, name='login'),
    url(r'^logout/$', logout, {"next_page": "/"}, name='logout'),
    url(r'^register/$', 'diffapp.views.register', name='register'),
    url(r'^chpasswd/$', password_change, {"template_name": "registration/chpasswd.html"}, name='chpasswd'),
    url(r'^chpasswd/done/$', password_change_done, {"template_name": "registration/chpasswd.html"}, name='chpasswd_done'),

    url(
        r'^get/to-review.py$',
        'diffapp.views.download_to_review',
        name='download_to_review'
    ),

    (r'^static/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.STATIC_ROOT}),

    # url(r'^diffserver/', include('diffserver.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
