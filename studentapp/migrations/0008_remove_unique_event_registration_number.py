from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('studentapp', '0007_eventregistration_team_fields_and_members'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='eventregistration',
            name='unique_event_registration_number',
        ),
    ]
