from django.contrib import admin
from django.urls import path
from django.conf.urls import include,url
from app.order import views
app_name ='[order]'
urlpatterns = [
    url(r'^$',views.orderplaceView.as_view(),name='place'),
    url(r'^commit$',views.ordercomitView.as_view(),name='commit'),
    url(r'^pay$',views.orderPayView.as_view(),name='pay'),
    url(r'^check$',views.CheckPayView.as_view(),name='check'),
    url(r'^comment/(?P<order_id>\d+)$',views.CommentView.as_view(),name='comment')
]
