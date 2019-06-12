from celery import Celery
from django.conf import settings
from django.template import loader
import os
import django
from django.core.mail import send_mail
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dailyfresh.settings')
django.setup()

from app.goods.models import GoodsType,IndexGoodsBanner,IndexPromotionBanner,IndexTypeGoodsBanner

app=Celery('celery_tasks',broker='redis://192.168.142.128:6379/3')
@app.task
def send_register_active_email(to_email,username,token):
    # 发送激活邮件，包含激活链接：http:127.0.0.1:8000/user/active/1
    subject = '天天水果欢迎信息'
    message = ''
    sender = settings.EMAIL_FROM
    receiver = [to_email]
    html_message = '<h1>尊敬的%s您好，欢迎您加入天天水果！祝您生活愉快，请点击下行链接激活您的帐号信息</h1><br/><a href="http://127.0.0.1:8000/user/active/%s">http://127.0.0.1:8000/user/active/%s</a>' % (
    username, token, token)
    send_mail(subject, message, sender, receiver, html_message=html_message)

@app.task
def generate_static_index_html():
    goodtypelist = GoodsType.objects.all()  # 类型
    goodsbanner = IndexGoodsBanner.objects.all()  # 滚动条
    promotionbanner = IndexPromotionBanner.objects.all()  # 活动
    # typegoodsbanner = IndexTypeGoodsBanner.objects.all()
    for type in goodtypelist:
        image_good = IndexTypeGoodsBanner.objects.filter(type=type, display_type=1).order_by('index')
        title_good = IndexTypeGoodsBanner.objects.filter(type=type, display_type=0).order_by('index')
        type.image_goods = image_good
        type.title_goods = title_good
        print(type.title_goods)

    sender = {'goodtypelist': goodtypelist, 'goodsbanner': goodsbanner, 'promotionbanner': promotionbanner}
    #使用模板1、加载模板文件，返回模板文件
    temp =loader.get_template('static_index.html')
    #2、模板渲染
    static_index_html = temp.render(sender)
    #3、生成首页对应静态文件
    save_path = os.path.join(settings.BASE_DIR,'static/index.html')
    with open(save_path,'w') as f:
        f.write(static_index_html)