from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import path
from django.conf.urls import include,url
from app.user.views import RegisterView,ActiveView,LoginView,LogoutView,UserInfoView,UserOrderView,UserAdressView
app_name ='[user]'
urlpatterns = [
    # url(r'^register$',views.register, name='register'),
    # url(r'^register_handle$',views.register_handle,name='resister_handle'),
    url(r'^register$',RegisterView.as_view(),name='register'),#注册
    url(r'^active/(?P<token>.*)$',ActiveView.as_view(),name='active'),#激活
    url(r'^login$',LoginView.as_view(),name='login'),#登录页面
    url(r'^logout$',LogoutView.as_view(),name='logout'),#退出界面
    url(r'^order/(?P<pindex>\d+)$',UserOrderView.as_view(),name='order'),
    url(r'^address$',UserAdressView.as_view(),name='address'),
    url(r'^$',UserInfoView.as_view(),name='info'),
]
