# Generated by Django 5.1.4 on 2024-12-12 14:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='breakdownrequest',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('pick_up', 'Pick up Completed'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('delivered', 'Delivered'), ('cancelled', 'Cancelled')], default='pending', max_length=20),
        ),
        migrations.AlterField(
            model_name='rating',
            name='rating',
            field=models.PositiveIntegerField(default=5),
        ),
        migrations.AlterField(
            model_name='serviceproviderprofile',
            name='profile_picture',
            field=models.ImageField(blank=True, default='profilepictures/default.png', null=True, upload_to='static/profilepictures/'),
        ),
    ]
