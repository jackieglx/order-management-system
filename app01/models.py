from django.db import models
from django.core.validators import RegexValidator

# Create your models here.
class ActiveBaseModel(models.Model):
    active = models.SmallIntegerField(verbose_name="状态", default=1, choices=((1, "激活"), (0, "删除")))
# 这张表是用来让别的类使用这个属性，而不用每个类都写一遍
# 这样每个类都可以做逻辑删除，而不是真正的删除（比如要删除一个管理员，逻辑上删除就行了，就是把管理员的状态由1激活变成0删除
    class Meta:
        abstract = True

# 但是我们不希望ActiveBaseModel再单独生成一个表，写abstract = True就把这个类当成基类，不会生成表了

class Administrator(ActiveBaseModel):
    """管理员表"""
    username = models.CharField(verbose_name="用户名", max_length=32, db_index=True)
    password = models.CharField(verbose_name="密码", max_length=64)
    mobile = models.CharField(verbose_name="手机号", max_length=11, db_index=True)
    create_date = models.DateTimeField(verbose_name="创建日期", auto_now_add=True)

class Level(ActiveBaseModel):
    """级别表"""
    title = models.CharField(verbose_name="标题", max_length=32)
    percent = models.IntegerField(verbose_name="折扣", help_text="填入0-100整数表示百分比，例如：90，表示90%")

    def __str__(self):
        return self.title

# Q：为什么级别需要单独关联一张表？
# A：当级别经常需要变动的时候（比如增加一个级别，删除某一个级别），就需要再创建一张级别的表
#   如果级别经常变动，就可以在Customer这张表里写成下面这样
    # level_choice = (
    #     (1, "vip"),
    #     (2, "vvip"),
    #     (3, "svip"),
    # )
    # level = models.SmallIntegerField("级别", choices=level_choice)

class Customer(ActiveBaseModel):
    """客户表"""
    username = models.CharField(verbose_name="用户名", max_length=32, db_index=True)
    password = models.CharField(verbose_name="密码", max_length=64)
    mobile = models.CharField(verbose_name="手机号", max_length=11, db_index=True, validators=[RegexValidator(r'^\d{11}$', '手机号格式错误'), ],)
    balance = models.DecimalField(verbose_name="账户余额", default=0, max_digits=10, decimal_places=2)
    level = models.ForeignKey(verbose_name="级别",to="Level", on_delete=models.CASCADE)
    create_date = models.DateTimeField(verbose_name="创建日期", auto_now_add=True)
    creator = models.ForeignKey(verbose_name="创建者", to="Administrator", on_delete=models.CASCADE) #用来记录当前这个客户是哪个管理员邀请的（创建的）


class PricePolicy(ActiveBaseModel):
    """价格策略表"""
    #  比如下单1000条，10块钱；2000条，18块钱
    count = models.IntegerField(verbose_name="数量")
    price = models.DecimalField(verbose_name="价格", default=0, max_digits=10, decimal_places=2)

class Order(ActiveBaseModel):
    """订单表"""
    status_choices = (
        (1, "待执行"),
        (2, "正在执行"),
        (3, "已完成"),
        (4, "失败"),
    )
    status = models.SmallIntegerField(verbose_name="状态", choices=status_choices, default=1)

    oid = models.CharField(verbose_name="订单号", max_length=64, unique=True)
    url = models.URLField(verbose_name="视频地址", db_index=True)
    count = models.IntegerField(verbose_name="数量")

    price = models.DecimalField(verbose_name="价格", default=0, max_digits=10, decimal_places=2)
    real_price = models.DecimalField(verbose_name="实际价格", default=0, max_digits=10, decimal_places=2)

    old_view_count = models.CharField(verbose_name="原播放量", max_length=32, default="0")

    create_datetime = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    customer = models.ForeignKey(verbose_name="客户", to="Customer", on_delete=models.CASCADE, null=True, blank=True)
    memo = models.TextField(verbose_name="备注", null=True, blank=True)

class TransactionRecord(ActiveBaseModel):
    """ 交易记录 """
    charge_type_class_mapping = {
        1: "success",
        2: "danger",
        3: "default",
        4: "info",
        5: "primary",
    }
    charge_type_choices = ((1, "充值"), (2, "扣款"), (3, "创建订单"), (4, "删除订单"), (5, "撤单"),)
    charge_type = models.SmallIntegerField(verbose_name="类型", choices=charge_type_choices)

    customer = models.ForeignKey(verbose_name="客户", to="Customer", on_delete=models.CASCADE)
    amount = models.DecimalField(verbose_name="金额", default=0, max_digits=10, decimal_places=2)

    creator = models.ForeignKey(verbose_name="管理员", to="Administrator", on_delete=models.CASCADE, null=True, blank=True)

    order_oid = models.CharField(verbose_name="订单号", max_length=64, null=True, blank=True, db_index=True)
    create_datetime = models.DateTimeField(verbose_name="交易时间", auto_now_add=True)
    memo = models.TextField(verbose_name="备注", null=True, blank=True)