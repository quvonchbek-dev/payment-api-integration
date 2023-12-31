# Generated by Django 4.2.5 on 2023-11-01 01:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payment_api', '0008_alter_paymetransaction_order'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='paymetransaction',
            name='time',
        ),
        migrations.AddField(
            model_name='paymetransaction',
            name='reason',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='paymetransaction',
            name='state',
            field=models.IntegerField(default=1),
        ),
        migrations.AlterField(
            model_name='paymetransaction',
            name='cancel_time',
            field=models.PositiveBigIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='paymetransaction',
            name='create_time',
            field=models.PositiveBigIntegerField(),
        ),
        migrations.AlterField(
            model_name='paymetransaction',
            name='perform_time',
            field=models.PositiveBigIntegerField(blank=True, null=True),
        ),
    ]
