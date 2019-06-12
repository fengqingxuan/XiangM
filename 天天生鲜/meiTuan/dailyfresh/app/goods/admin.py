from django.contrib import admin
from app.goods.models import GoodsType,Goods,GoodsSKU,IndexGoodsBanner,IndexTypeGoodsBanner,IndexPromotionBanner
# Register your models here.
admin.site.register(GoodsType)
admin.site.register(Goods)
admin.site.register(GoodsSKU)
admin.site.register(IndexGoodsBanner)
admin.site.register(IndexTypeGoodsBanner)
admin.site.register(IndexPromotionBanner)