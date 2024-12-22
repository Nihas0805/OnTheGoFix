# Generated by Django 5.1.4 on 2024-12-22 18:18

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0009_alter_breakdownrequest_description_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='breakdownrequest',
            name='service_provider',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assigned_requests', to=settings.AUTH_USER_MODEL),
        ),
    ]
