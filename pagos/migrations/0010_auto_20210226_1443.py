# Generated by Django 3.1.6 on 2021-02-26 17:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pagos', '0009_pagowebpay_amount'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ordencompra',
            name='token_webpay',
            field=models.CharField(max_length=200, null=True),
        ),
    ]
