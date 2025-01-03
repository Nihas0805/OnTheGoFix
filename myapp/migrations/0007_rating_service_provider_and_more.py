# Generated by Django 5.1.4 on 2024-12-20 17:46

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0006_alter_breakdownrequest_description'),
    ]

    operations = [
        migrations.AddField(
            model_name='rating',
            name='service_provider',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='ratings', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='serviceproviderprofile',
            name='average_rating',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='serviceproviderprofile',
            name='total_reviews',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
