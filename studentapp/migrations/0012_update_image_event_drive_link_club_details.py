from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('studentapp', '0011_batch_competition_score'),
    ]

    operations = [
        migrations.AddField(
            model_name='update',
            name='image',
            field=models.ImageField(blank=True, upload_to='updates/'),
        ),
        migrations.AddField(
            model_name='event',
            name='drive_link',
            field=models.URLField(blank=True, help_text='Optional Google Drive link for event photos'),
        ),
        migrations.AddField(
            model_name='club',
            name='description',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='club',
            name='foundation_members',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='club',
            name='guide',
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name='club',
            name='rules_and_regulations',
            field=models.TextField(blank=True),
        ),
    ]
