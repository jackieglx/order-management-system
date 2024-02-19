# Generated by Django 3.2 on 2024-02-18 05:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app01', '0005_order_pricepolicy_transactions'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.SmallIntegerField(choices=[(4, '失败'), (2, '正在执行'), (3, '已完成'), (1, '待执行')], default=1, verbose_name='状态'),
        ),
    ]
