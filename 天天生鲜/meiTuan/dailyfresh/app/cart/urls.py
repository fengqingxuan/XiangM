from django.contrib import admin
from django.urls import path
from django.conf.urls import include,url
from app.cart import views
app_name ='[cart]'
urlpatterns = [
    url(r'^add$',views.CarAddView.as_view(),name='add'),
    url(r'^$',views.CarInfoView.as_view(),name='show'),
    url(r'^update$',views.CarUpdateView.as_view(),name='update'),
    url(r'^delete$',views.CartDeleView.as_view(),name='delete'),
]
