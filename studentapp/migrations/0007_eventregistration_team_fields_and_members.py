from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('studentapp', '0006_event_allow_registration_and_eventregistration'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventregistration',
            name='performance_type',
            field=models.CharField(
                choices=[('solo', 'Solo'), ('team', 'Team')],
                default='solo',
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name='eventregistration',
            name='team_size',
            field=models.PositiveSmallIntegerField(default=1),
        ),
        migrations.CreateModel(
            name='EventRegistrationMember',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, blank=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, blank=True, null=True)),
                ('full_name', models.CharField(max_length=160)),
                ('registration_number', models.CharField(max_length=50)),
                ('batch_name', models.CharField(max_length=80)),
                ('order', models.PositiveSmallIntegerField(default=1)),
                ('registration', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='members', to='studentapp.eventregistration')),
            ],
            options={
                'ordering': ['order', 'full_name'],
            },
        ),
        migrations.AddConstraint(
            model_name='eventregistrationmember',
            constraint=models.UniqueConstraint(
                fields=('registration', 'registration_number'),
                name='unique_member_regnum_per_submission',
            ),
        ),
    ]
