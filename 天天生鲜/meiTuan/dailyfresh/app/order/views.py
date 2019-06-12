from django.shortcuts import render,redirect
from django.urls import reverse
from django.views.generic import View
from utils.mixin import LoginRequiredMixin
from app.goods.models import GoodsSKU
from app.user.models import Address
from app.order.models import OrderInfo,OrderGoods
from django.http import HttpResponse,JsonResponse
from django_redis import get_redis_connection
from datetime import datetime
from django.db import transaction
from django.conf import settings
import os
from alipay import AliPay

# Create your views here.

class orderplaceView(LoginRequiredMixin,View):
    def post(self,request):
        user=request.user
        sku_list=request.POST.getlist('skuul')
        if not sku_list:
            redirect(reverse('cart:show'))
        skus=[]
        total_amount=0
        total_price=0
        pay_way=10
        total=0
        conn=get_redis_connection('default')
        cartkey='cart_%d'%user.id
        for id in sku_list:
            sku=GoodsSKU.objects.get(id=id)
            count=conn.hget(cartkey,id)
            smallprice=sku.price*int(count)
            sku.smallprice=smallprice
            sku.count=int(count)
            skus.append(sku)
            total_amount += int(count)
            total_price+=smallprice
        skulist=','.join(sku_list)
        total=total_price+pay_way
        addrs=Address.objects.filter(user=user)
        content={
            'skus':skus,
            'addrs':addrs,
            'total_amount':total_amount,
            'total_price':total_price,
            'pay_way':pay_way,
            'total':total,
            'skulist':skulist
        }
        return render(request,'place_order.html',content)


class ordercomitView(LoginRequiredMixin,View):
    @transaction.atomic
    def post(self,request):
        user=request.user
        conn=get_redis_connection('default')
        cartkey='cart_%d'%user.id
        addrid=request.POST.get('addr')
        pay_method=request.POST.get('pay_style')
        skulist=request.POST.get('skulist')
        transit=request.POST.get('transit')
#校验入参
        if not all([addrid,pay_method,skulist]):
            return JsonResponse({'res':-1,'errmsg':'入参不正确'})
        try:
            addr=Address.objects.get(id=addrid)
        except Address.DoesNotExist:
            return JsonResponse({'res':-2,'errmsg':'不存在的地址信息'})
        if pay_method not in OrderInfo.PAY_METHOD.keys():
            return JsonResponse({'res':-3,'errmsg':'支付方式有误'})
        sku_list=skulist.split(',')
        total_count=0
        total_price=0
        #生成订单id
        order_id=datetime.now().strftime('%Y%m%d%H%M%S')+str(user.id)
        save_id=transaction.savepoint()
        #生成订单对象
        try:
            order=OrderInfo.objects.create(order_id=order_id,
                                     user=user,
                                     addr=addr,
                                     pay_method=pay_method,
                                     total_count=total_count,
                                     total_price=total_price,
                                     transit_price=transit)
            for skuid in sku_list:
                for i in range(3):
                    try:
                        sku=GoodsSKU.objects.get(id=skuid)
                    except GoodsSKU.DoesNotExist:
                        transaction.savepoint_rollback(save_id)
                        return JsonResponse({'res':-4,'errmsg':'没有该商品'})
                    count=conn.hget(cartkey,skuid)
                    amount=int(count)*sku.price
                    if int(count)>sku.stock:
                        transaction.savepoint_rollback(save_id)
                        return JsonResponse({'res':-5,'errmsg':'商品库存不足'})
                    origin_stock = sku.stock
                    print('user:%d,time:%d,stock:%d'%(user.id,i,origin_stock))
                    new_stock = origin_stock - int(count)
                    new_sales = sku.sales + int(count)
                    res = GoodsSKU.objects.filter(id=skuid, stock=origin_stock).update(stock=new_stock, sales=new_sales)
                    if res == 0:
                        if i == 2:
                            transaction.savepoint_rollback(save_id)
                            return JsonResponse({'res': -6, 'errmsg': '下单失败'})
                        continue
                    #生成订单商品对象
                    OrderGoods.objects.create(order=order,
                                              sku=sku,
                                              count=int(count),
                                              price=amount)
                    total_count += int(count)
                    total_price += amount
                    #sku.sales+=int(count)#修改SKU商品销量
                    #sku.stock-=int(count)#修改SKU商品库存
                    #sku.save()
                    break
            order.total_count=total_count
            order.total_price=total_price
            order.save()
        except Exception as e:
            transaction.savepoint_rollback(save_id)
        #清除购物车
        transaction.savepoint_commit(save_id)
        conn.hdel(cartkey,*sku_list)
        return JsonResponse({'res':1,'message':' 订单生成成功'})


class orderPayView(View):
    def post(self,request):
        user=request.user
        if not user.is_authenticated:
            return JsonResponse({'res':-1,'errmsg':'用户未登录'})
        order_id=request.POST.get('order_id')
        if not order_id:
            return JsonResponse({'res':-2,'errmsg':'订单信息有误'})
        try:
            order=OrderInfo.objects.get(order_id=order_id,
                                        user=user,
                                        order_status=1,
                                        pay_method=3)
        except OrderInfo.DoesNotExist as e:
            return JsonResponse({'res':-3,'errmsg':'不存在订单'})
        amount=order.total_price+order.transit_price
        title='天天生鲜订单%s'%order_id

        alipay=AliPay(
            appid="2016092900625903", #应用id
            app_notify_url=None,       #默认回调url
            app_private_key_path=os.path.join(settings.BASE_DIR,'app/order/app_private_key.pem'),     #个人私钥地址
            alipay_public_key_path=os.path.join(settings.BASE_DIR,'app/order/alipay_public_key.pem'),   #支付宝公钥地址
            sign_type="RSA2",          #RSA或RSA2
            debug=True                  #默认False，沙箱用True
        )
        #电脑网战支付
        order_string=alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,  #订单id
            total_amount=str(amount),    #总金额
            subject=title,          #标题
            return_url=None,        #同步回调地址
            notify_url=None         #异步回调地址
        )
        #返回应答-客户支付页面
        pay_url='https://openapi.alipaydev.com/gateway.do?'+order_string
        return JsonResponse({'res':1,'message':pay_url})


class CheckPayView(View):
    def post(self,request):
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': -1, 'errmsg': '用户未登录'})
        order_id = request.POST.get('order_id')
        if not order_id:
            return JsonResponse({'res': -2, 'errmsg': '订单信息有误'})
        try:
            order = OrderInfo.objects.get(order_id=order_id,
                                          user=user,
                                          order_status=1,
                                          pay_method=3)
        except OrderInfo.DoesNotExist as e:
            return JsonResponse({'res': -3, 'errmsg': '不存在订单'})
        amount = order.total_price + order.transit_price
        title = '天天生鲜订单%s' % order_id

        alipay = AliPay(
            appid="2016092900625903",  # 应用id
            app_notify_url=None,  # 默认回调url
            app_private_key_path=os.path.join(settings.BASE_DIR, 'app/order/app_private_key.pem'),  # 个人私钥地址
            alipay_public_key_path=os.path.join(settings.BASE_DIR, 'app/order/alipay_public_key.pem'),  # 支付宝公钥地址
            sign_type="RSA2",  # RSA或RSA2
            debug=True  # 默认False，沙箱用True
        )
        while True:
            response=alipay.api_alipay_trade_query(order_id)
            code=response.get('code')
            if code=='10000' and response.get('trade_status')=='TRADE_SUCCESS':
                #支付成功
                trade_no=response.get('trade_no')
                order.trade_no=trade_no
                order.order_status=4
                order.save()
                return JsonResponse({'res':1,'message':'支付成功'})
            elif code =='40004' or (code =='10000' and response.get('trade_status') == 'WAIT_BUYER_PAY'):
                import time
                time.sleep(5)
                continue
            else:
                return JsonResponse({'res':-4,'errmsg':'付款失败'})


class CommentView(LoginRequiredMixin,View):
    def get(self,request,order_id):
        user=request.user
        if not order_id:
            return redirect(reverse('user:order'))
        try:
            order=OrderInfo.objects.get(order_id=order_id,user=user)
        except OrderInfo.DoesNotExist as e:
            return redirect(reverse('user:order'))
        order.status_name=order.ORDER_STATUS.get(order.order_status)
        order_skus=OrderGoods.objects.filter(order=order)
        order.order_skus=order_skus
        content={'order':order}
        return render(request,'order_comment.html',content)
    def post(self,request,order_id):
        user=request.user
        order_id=request.POST.get('order_id')
        if not order_id:
            return redirect(reverse('user:order',kwargs={'pindex':1}))
        try:
            order=OrderInfo.objects.get(order_id=order_id,user=user)
        except OrderInfo.DoesNotExist as e:
            return redirect(reverse('user:order',kwargs={'pindex':1}))
        total_count=request.POST.get('total_count')
        for i in range(1,int(total_count)+1):
            sku_id=request.POST.get('sku_%d'%i)
            try:
                sku=GoodsSKU.objects.get(id=sku_id)
            except GoodsSKU.DoesNotExist as e:
                return redirect(reverse('user:order',kwargs={'pindex':1}))
            comment=request.POST.get('content_%d'%i)
            order_sku=OrderGoods.objects.get(order=order,
                                   sku=sku)
            order_sku.comment=comment
            order_sku.save()
        order.order_status=5
        order.save()
        return redirect(reverse('user:order',kwargs={'pindex':1}))
