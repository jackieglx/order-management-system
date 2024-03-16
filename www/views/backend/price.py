from www import models
from utils.v3 import BaseCurd


class Price(BaseCurd):
    # 列表配置
    queryset = models.PricePolicy.objects.filter().order_by("count")
    table_header = ["数量", "价格"]
    table_field = [
        ("db", "count"),
        ("func", lambda req, ins: f"¥{ins.price}"),
    ]

    #  新增和编辑配置
    base_form_model = models.PricePolicy
    base_form_fields = ["count", "price"]
