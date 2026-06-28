from django.db import migrations
from django.db import models


FIXED_INFO_CATEGORIES = [
    ('University Updates', 'info-one', 0),
    ('NSS Updates', 'info-two', 1),
    ('Hostel Updates', 'info-three', 2),
]


def seed_fixed_info_categories(apps, schema_editor):
    InfoCategory = apps.get_model('studentapp', 'InfoCategory')
    active_category_ids = []

    for title, style_class, order in FIXED_INFO_CATEGORIES:
        category = (
            InfoCategory.objects.exclude(id__in=active_category_ids)
            .filter(style_class=style_class)
            .order_by('order', 'id')
            .first()
            or InfoCategory.objects.exclude(id__in=active_category_ids)
            .filter(title=title)
            .order_by('order', 'id')
            .first()
        )

        if category is None:
            category = InfoCategory()

        category.title = title
        category.subtitle = ''
        category.style_class = style_class
        category.order = order
        category.is_active = True
        category.save()
        active_category_ids.append(category.id)

    InfoCategory.objects.exclude(id__in=active_category_ids).update(is_active=False)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('studentapp', '0004_delete_aboutcontent'),
    ]

    operations = [
        migrations.AlterField(
            model_name='infocategory',
            name='style_class',
            field=models.CharField(
                choices=[
                    ('info-one', 'University Updates'),
                    ('info-two', 'NSS Updates'),
                    ('info-three', 'Hostel Updates'),
                ],
                default='info-one',
                max_length=20,
            ),
        ),
        migrations.RunPython(seed_fixed_info_categories, noop_reverse),
    ]
