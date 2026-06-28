from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('studentapp', '0005_fixed_info_categories'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='allow_student_registration',
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name='EventRegistration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, blank=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, blank=True, null=True)),
                ('full_name', models.CharField(max_length=160)),
                ('registration_number', models.CharField(max_length=50)),
                ('batch_name', models.CharField(max_length=80)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='registrations', to='studentapp.event')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='eventregistration',
            constraint=models.UniqueConstraint(fields=('event', 'registration_number'), name='unique_event_registration_number'),
        ),
    ]
