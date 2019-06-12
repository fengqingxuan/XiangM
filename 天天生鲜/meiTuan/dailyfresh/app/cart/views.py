from django.shortcuts import render
from django.views.generic import View
from django.http import JsonResponse
from app.goods.models import GoodsSKU
from django_redis import get_redis_connection
from utils.mixin import LoginRequiredMixin
# Create your views here.

class CarAddView(View):
    def post(self,request):
        #校验是否登录
        user=request.user
        if not user.is_authenticated:
            return JsonResponse({'res':0,'errmag':'用户未登录！'})
        #获得值
        good_id=request.POST.get('good_id')
        count=request.POST.get('count')
        #校验值存在
        if not all([good_id,count]):
            return JsonResponse({'res':-1,'errmag':'数据不完整！'})
        #校验数量正确
        try:
            count=int(count)
        except Exception as e:
            return JsonResponse({'res':-2,'errmag':'商品数量不正确！'})
        #校验商品id存在
        try:
            good=GoodsSKU.objects.get(id=good_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res':-3,'errmag':'没有此商品！'})
        conn=get_redis_connection('default')
        carkey='cart_%d'%user.id
        #取得默认数目
        car_count=conn.hget(carkey,good_id)
        if car_count:
            count+=int(car_count)
        #验证数量不越界
        if count>good.stock:
            return JsonResponse({'res':-4,'errmag':'数量超过库存，添加失败！'})
        conn.hset(carkey,good_id,count)
        total=conn.hlen(carkey)
        print(gooscount)
        return JsonResponse({'res':'1','message':'添加成功！','total':total})

class CarInfoView(LoginRequiredMixin,View):
    def get(self,request):
        user=request.user
        cartkey='cart_%d'%user.id
        conn=get_redis_connection()
        cart_dict = conn.hgetall(cartkey)
        skulist=[]
        total_count=0
        total_price=0
        for sku_id,count in cart_dict.items():
            sku=GoodsSKU.objects.get(id=sku_id)
            amount=sku.price*int(count)
            sku.amount=amount
            sku.count=int(count)
            skulist.append(sku)
            total_count+=int(count)
            total_price+=amount
        params={
            'total_count':total_count,
            'total_price':total_price,
            'skulist':skulist
        }
        return render(request,'cart.html',params)

class CarUpdateView(View):
    def post(self,request):
        user=request.user
        if not user.is_authenticated:
            return JsonResponse({'res':0,'errmsg':'用户未登录！'})
        sku_id=request.POST.get('sku_id')
        count=request.POST.get('count')
        if not all([sku_id,count]):
            return JsonResponse({'res':-1,'errmsg':'输入参数有误！'})
        try:
            count=int(count)
        except Exception:
            return JsonResponse({'res':-2,'errmsg':'输入数量有误！'})
        try:
            sku=GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res':-3,'errmsg':'没有所选择的商品！'})
        if count>sku.stock:
            return JsonResponse({'res':-4,'errmsg':'商品所选数目超范围'})
        carkey='cart_%d'%user.id
        conn=get_redis_connection()
        conn.hset(carkey,sku_id,count)
        goosamount=0
        cartlist=conn.hvals(carkey)
        for car in cartlist:
            goosamount+=int(car)
        return JsonResponse({'res':1,'message':'添加成功！','goosamount':goosamount})

class CartDeleView(View):
    def post(self,request):
        user=request.user
        if not user.is_authenticated:
            return JsonResponse({'res':0,'errmsg':'用户未登录！'})
        sku_id=request.POST.get('sku_id')
        if not all([sku_id]):
            return JsonResponse({'res':-1,'errmsg':'输入参数有误！'})
        try:
            sku=GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res':-2,'errmsg':'没有所选择的商品！'})
        conn=get_redis_connection('default')
        cartkey='cart_%d'%user.id
        conn.hdel(cartkey,sku_id)
        goosamount = 0
        cartlist = conn.hvals(cartkey)
        for car in cartlist:
            goosamount += int(car)
        return JsonResponse({'res':1,'message':'删除成功！','goosamount':goosamount})

