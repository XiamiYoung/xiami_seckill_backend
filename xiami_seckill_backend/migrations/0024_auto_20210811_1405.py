# Generated by Django 3.2.5 on 2021-08-11 06:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('xiami_seckill_backend', '0023_jdorder_stock_count'),
    ]

    operations = [
        migrations.AddField(
            model_name='jdorder',
            name='current_price',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='jdorder',
            name='original_price',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='jdorder',
            name='saved_price',
            field=models.IntegerField(default=0),
        ),
    ]
