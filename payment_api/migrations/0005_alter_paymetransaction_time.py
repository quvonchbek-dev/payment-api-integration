# Generated by Django 4.2.5 on 2023-10-27 17:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payment_api', '0004_tarif_alter_payment_options_user_send_group_link_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='paymetransaction',
            name='time',
            field=models.FloatField(),
        ),
    ]
