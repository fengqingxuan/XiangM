from django.contrib import admin
from django.urls import path
from django.conf.urls import include,url
from app.goods import views
app_name ='[goods]'
urlpatterns = [
    url(r'^$',views.IndexView.as_view(),name='index'),
    url(r'^detail/(?P<sku_id>\d+)$',views.DetailView.as_view(),name='detail'),
    url(r'^list/(?P<typeid>\d+)/(?P<pagenum>\d+)$',views.ListView.as_view(),name='list')
]
