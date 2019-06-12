from django.shortcuts import render,redirect
from django.urls import reverse
from utils.mixin import LoginRequiredMixin
from django.views.generic import View
from app.goods.models import GoodsType,IndexGoodsBanner,IndexPromotionBanner,IndexTypeGoodsBanner,GoodsSKU
from app.order.models import OrderGoods
from django_redis import get_redis_connection
from django.core.paginator import Paginator
# Create your views here.
class IndexView(View):
    def get(self,request):
        goodtypelist = GoodsType.objects.all()      #类型
        goodsbanner = IndexGoodsBanner.objects.all()    #滚动条
        promotionbanner = IndexPromotionBanner.objects.all()    #活动
       # typegoodsbanner = IndexTypeGoodsBanner.objects.all()
        for type in goodtypelist:
            image_good = IndexTypeGoodsBanner.objects.filter(type=type,display_type=1).order_by('index')
            title_good = IndexTypeGoodsBanner.objects.filter(type=type,display_type=0).order_by('index')
            type.image_goods = image_good
            type.title_goods = title_good
            print(type.title_goods)
        user=request.user
        cart_count=0
        if user.is_authenticated:
            #已登录
            conn=get_redis_connection('default')
            cart_key='cart_%d'%user.id
            cart_count=conn.hlen(cart_key)
        sender = {'goodtypelist': goodtypelist, 'goodsbanner': goodsbanner, 'promotionbanner': promotionbanner,'cart_count':cart_count}

        return render(request, 'index.html', sender)

class DetailView(View):
    def get(self,request,sku_id):
        goodtypelist = GoodsType.objects.all()
        try:
            good_sku=GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            redirect(reverse('goods:index'))
        goods_comment=OrderGoods.objects.filter(sku=good_sku).exclude(comment='')
        new_goods=GoodsSKU.objects.filter(type=good_sku.type).order_by('-create_time')[:2]
        same_spu_skus=GoodsSKU.objects.filter(goods=good_sku.goods).exclude(id=sku_id)
        user=request.user
        cart_count=0
        if user.is_authenticated:
            conn=get_redis_connection('default')
            cart_key='cart_%d'%user.id
            cart_count=conn.hlen(cart_key)
            historykey='history_%d'%user.id
            conn.lrem(historykey,0,sku_id)
            conn.lpush(historykey,sku_id)
            conn.ltrim(historykey,0,4)
        params={
            'goodtypes':goodtypelist,
            'good_sku':good_sku,
            'goods_comment':goods_comment,
            'new_goods':new_goods,
            'cart_count':cart_count,
            'same_spu_skus':same_spu_skus
        }
        return render(request,'detail.html',params)
# /list/typeid/pagenum?order='' default 默认 ， price 价格 ， hot 人气
class ListView(View):
    def get(self,request,typeid,pagenum):
        try:
            type=GoodsType.objects.get(id=typeid)
        except GoodsType.DoesNotExist:
            return redirect(reverse('goods:index'))
        goodtypes=GoodsType.objects.all()
        order=request.GET.get('order')
        if order=='price':
            good_sku = GoodsSKU.objects.filter(type=typeid).order_by('-price')
        elif order=='hot':
            good_sku = GoodsSKU.objects.filter(type=typeid).order_by('-sales')
        else:
            order='default'
            good_sku = GoodsSKU.objects.filter(type=typeid).order_by('-id')
        paginator=Paginator(good_sku,1)
        try:
            page=int(pagenum)
        except Exception as e:
            page=1
        if page>paginator.num_pages:
            page=1
        sku_page=paginator.page(page)
        num_page=paginator.num_pages
        if num_page<5:
            pages = range(1,num_page+1)
        elif page<=3:
            pages = range(1,6)
        elif num_page-page<=2:
            pages = range(num_page-4,num_page+1)
        else:
            pages = range(page-2,page+3)
        #新品
        new_sku=GoodsSKU.objects.filter(type=type).order_by('-update_time')[:2]
        user=request.user
        car_count=0
        if user.is_authenticated:
            conn=get_redis_connection('default')
            carrkey='car_%d'%user.id
            car_count=conn.hlen(carrkey)
        message={
            'type':type,
            'goodtypes':goodtypes,
            'sku_page':sku_page,
            'new_sku':new_sku,
            'cart_count':car_count,
            'order':order,
            'pages':pages
        }
        return render(request,'list.html',message)