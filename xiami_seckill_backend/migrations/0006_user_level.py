# Generated by Django 3.0.8 on 2021-06-26 02:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('xiami_seckill_backend', '0005_auto_20210626_1054'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='level',
            field=models.CharField(default='1', max_length=20),
        ),
    ]
