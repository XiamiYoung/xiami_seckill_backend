# Generated by Django 3.2.5 on 2021-08-10 12:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('xiami_seckill_backend', '0022_auto_20210810_1423'),
    ]

    operations = [
        migrations.AddField(
            model_name='jdorder',
            name='stock_count',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
    ]
