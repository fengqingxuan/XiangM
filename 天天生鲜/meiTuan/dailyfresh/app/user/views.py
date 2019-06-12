from django.shortcuts import render,redirect
from django.urls import reverse
from django.views.generic import View
from django.contrib.auth import authenticate,login,logout
from app.user.models import User,Address
from django.conf import settings
from django.http import HttpResponse
from django.core.mail import send_mail
from django.core.paginator import Paginator
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from celery_tasks.tasks import send_register_active_email
from utils.mixin import LoginRequiredMixin
from django_redis import get_redis_connection
from app.goods.models import GoodsSKU
from app.order.models import OrderInfo,OrderGoods
import re
# Create your views here.

#/user/register
def register(request):
    #显示注册页面
    if request.method=='GET':
        return render(request,'register.html')
    else:
        '''进行注册的处理'''
        # 接受数据
        username = request.POST.get("user_name")
        password = request.POST.get("pwd")
        email = request.POST.get("email")
        allow = request.POST.get('allow')

        # 数据校验
        if not all([username, password, email]):
            # 数据不完整
            return render(request, 'register.html', {'errmsg': '数据不完整'})
        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})
        if allow != 'on':
            return render(request, 'register.html', {'errmsg': '请同意协议'})
        # 检验用户是否重复
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = None

        if user:
            return render(request, 'register.html', {'errmsg': '用户名已存在！'})

        # 业务处理/用户注册
        user = User.objects.create_user(username, email, password)
        user.is_active = 0
        user.save()

        # 返回应答，跳转到首页
        return redirect(reverse('goods:index'))
#
def register_handle(request):
#     '''进行注册的处理'''
#     #接受数据
#     username = request.POST.get("user_name")
#     password = request.POST.get("pwd")
#     email = request.POST.get("email")
#     allow = request.POST.get('allow')
#
#     #数据校验
#     if not all([username, password, email]):
#         #数据不完整
#         return render(request,'register.html',{'errmsg':'数据不完整'})
#     if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$',email):
#         return render(request,'register.html',{'errmsg':'邮箱格式不正确'})
#     if allow !='on':
#         return render(request,'register.html',{'errmsg':'请同意协议'})
#     #检验用户是否重复
#     try:
#         user=User.objects.get(username=username)
#     except User.DoesNotExist:
#         user=None
#
#     if user:
#         return render(request,'register.html',{'errmsg':'用户名已存在！'})
#
#     #业务处理/用户注册
#     user= User.objects.create_user(username,email,password)
#     user.is_active=0
#     user.save()
#
#     #返回应答，跳转到首页
    return redirect(reverse('goods:index'))

class RegisterView(View):
    def get(self,request):
        return render(request,'register.html')
    def post(self,request):
        '''进行注册的处理'''
        # 接受数据
        username = request.POST.get("user_name")
        password = request.POST.get("pwd")
        email = request.POST.get("email")
        allow = request.POST.get('allow')

        # 数据校验
        if not all([username, password, email]):
            # 数据不完整
            return render(request, 'register.html', {'errmsg': '数据不完整'})
        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})
        if allow != 'on':
            return render(request, 'register.html', {'errmsg': '请同意协议'})
        # 检验用户是否重复
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = None

        if user:
            return render(request, 'register.html', {'errmsg': '用户名已存在！'})

        # 业务处理/用户注册
        user = User.objects.create_user(username, email, password)
        user.is_active = 0
        user.save()
        # 激活链接中需要包含用户的身份信息,并且把身份信息进行加密
        # 加密用户信息，生成激活token
        serializer = Serializer(settings.SECRET_KEY, 3600)
        info = {'confirm': user.id}
        token = serializer.dumps(info)
        token = token.decode('utf-8')
        #celery发送邮件
        send_register_active_email.delay(email,username,token)

        # 返回应答，跳转到首页
        return redirect(reverse('goods:index'))

class ActiveView(View):
    def get(self,request,token):
        serializer = Serializer(settings.SECRET_KEY,3600)
        print("qqq"+token)
        try:
            info=serializer.loads(token)
            user_id=info['confirm']
            user=User.objects.get(id=user_id)
            user.is_active=1
            user.save()
            return redirect(reverse('user:login'))
        except SignatureExpired as e:
            return HttpResponse('激活链接已过期')

class LoginView(View):
    def get(self,request):
        print(request.session)
        # if 'ifclient' in request.COOKIES:
        #     #return redirect(reverse('goods:index'))
        #     return render(request, 'login.html')
        # else:
        if 'username' in request.COOKIES:
            username = request.COOKIES['username']
            checked='checked'
        else:
            username=''
            checked=''
        return render(request,'login.html',{'username':username,'checked':checked})
    def post(self,request):
        #获取数据
        username=request.POST.get('username')
        password=request.POST.get('pwd')
        remem = request.POST.get('remem')
        print(str(username)+":"+str(password))
        #数据验证
        if not all([username,password]):
           return render(request,'login.html',{'esmag':'有未填参数！'})
        #数据处理
        user=authenticate(username=username,password=password)
        print(user)
        if user is not None:
            if user.is_active:
                login(request,user)
                next_url=request.GET.get('next',reverse('goods:index'))
                print(next_url)
                url=redirect(next_url)
                url.set_cookie('ifclient', True)
                if str(remem)=='on':
                    url.set_cookie('username',username,max_age=12*24*3600)
                else:
                    url.delete_cookie('username')
                return url
            else:
                return render(request,'login.html',{'esmag':'账户未激活！'})
        else:
            return render(request, 'login.html', {'esmag': '账户或密码有误！'})
        #跳转
        return render(request,'login.html')
#退出登录
class LogoutView(View):
    def get(self,request):
        logout(request)
        return redirect(reverse('goods:index'))
#/user
class UserInfoView(LoginRequiredMixin,View):
    def get(self,request):
        user=request.user
        addr=Address.objects.get_default_addr(user)
        conn=get_redis_connection('default')
        keys='history_%d'%user.id
        good_li=conn.lrange(keys,0,4)
        good_list=[]
        for i in good_li:
            good=GoodsSKU.objects.get(id=i)
            good_list.append(good)
        content={'page':'info','address':addr,'good_list':good_list}
        return render(request,'user_center_info.html',content)
#/user/order
class UserOrderView(LoginRequiredMixin,View):
    def get(self,request,pindex):
        user=request.user
        user_orders=OrderInfo.objects.filter(user=user).order_by('-create_time')
        for user_order in user_orders:
            order_skus=OrderGoods.objects.filter(order=user_order)
            user_order.order_skus=order_skus
            user_order.order_statu_name=OrderInfo.ORDER_STATUS[user_order.order_status]
        paginator=Paginator(user_orders,2)
        try:
            page=int(pindex)
        except Exception as e:
            page=1
        if page>paginator.num_pages:
            page=1
        order_pages=paginator.page(page)
        num_pages=paginator.num_pages
        if num_pages<5:
            pages=range(1,num_pages+1)
        elif page<=3:
            pages=range(1,6)
        elif num_pages-page<=2:
            pages=range(num_pages-4,num_pages+1)
        else:
            pages=range(page-2,page+3)
        content={'order_pages':order_pages,'pages':pages,'page':'order'}
        print(content)
        return render(request,'user_center_order.html',content)
#/user/address
class UserAdressView(LoginRequiredMixin,View):
    def get(self,request):
        #1.获得数据 2.数据验证 3.数据处理 4页面跳转
        user=request.user
        addr=Address.objects.get_default_addr(user)
        return render(request,'user_center_site.html',{'page':'address','addr':addr})
    def post(self,request):
        receiver=request.POST.get('receiver')
        address = request.POST.get('address')
        zip_code = request.POST.get('zip_code')
        phone = request.POST.get('phone')
        if not all([receiver,address,phone]):
            return render(request,'user_center_site.html',{'esmsg':'有未填参数'})
        print(type(re.match(r'^1[3456789]\d{9}$',phone)))
        if not re.match(r'^1[3456789]\d{9}$',phone):
            return render(request,'user_center_site.html',{'esmsg':'电话号码有误'})
        user = request.user
        addr = Address.objects.get_default_addr(user)
        if addr:
            is_default=False
        else:
            is_default=True
        Address.objects.create(user=user,receiver=receiver,addr=address,zip_code=zip_code,phone=phone,is_default=is_default)
        return redirect(reverse('user:address'))