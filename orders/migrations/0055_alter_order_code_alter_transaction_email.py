# Generated by Django 5.1.2 on 2025-03-05 14:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0054_alter_order_code_transaction'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='code',
            field=models.CharField(default='37UER2X7', max_length=20),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
    ]
