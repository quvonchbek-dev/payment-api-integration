# Generated by Django 4.2.5 on 2023-10-27 17:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payment_api', '0005_alter_paymetransaction_time'),
    ]

    operations = [
        migrations.AlterField(
            model_name='paymetransaction',
            name='time',
            field=models.DateTimeField(),
        ),
    ]