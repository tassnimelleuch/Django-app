"""Initial migration for the accounts app."""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    """Migration to create Contact and PhoneNumber models."""

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Contact',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True,
                    primary_key=True,
                    serialize=False,
                    verbose_name='ID'
                )),
                ('first_name', models.CharField(max_length=100)),
                ('last_name', models.CharField(max_length=100)),
                ('email', models.EmailField(
                    blank=True,
                    max_length=254,
                    null=True
                )),
                ('linkedin', models.URLField(
                    blank=True,
                    null=True
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='contacts',
                    to=settings.AUTH_USER_MODEL
                )),
            ],
        ),
        migrations.CreateModel(
            name='PhoneNumber',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True,
                    primary_key=True,
                    serialize=False,
                    verbose_name='ID'
                )),
                ('phone_type', models.CharField(
                    choices=[
                        ('mobile', 'Mobile'),
                        ('home', 'Home'),
                        ('work', 'Work'),
                        ('other', 'Other')
                    ],
                    default='mobile',
                    max_length=20
                )),
                ('number', models.CharField(max_length=20)),
                ('contact', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='phone_numbers',
                    to='accounts.contact'
                )),
            ],
        ),
    ]
