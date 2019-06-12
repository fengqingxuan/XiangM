from haystack import indexes           #定义索引类
from app.goods.models import GoodsSKU  #导入模型类
#指定对于某个类的某些数据建立索引
class GoodsSKUIndex(indexes.SearchIndex, indexes.Indexable):
    #索引字段 use_template=True指定根据表中哪些字段建立索引文件的说明放在一个文件中
    text=indexes.CharField(document=True,use_template=True)
    def get_model(self):
        return GoodsSKU  #返回你的模型类
    def index_queryset(self,using=None):  #建立索引的数据
        return self.get_model().objects.all()