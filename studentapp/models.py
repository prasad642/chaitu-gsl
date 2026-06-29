from django.db import models


class Batch(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self):
        return self.name

class Competition(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self):
        return self.name

class Score(models.Model):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE)
    score = models.IntegerField()
    def __str__(self):
        return f"{self.batch} - {self.competition} ({self.score})"




class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        abstract = True


class HomeSlide(TimeStampedModel):
    title = models.CharField(max_length=120, blank=True)
    image = models.ImageField(upload_to='home/slides/')
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.title or f'Home slide {self.pk}'


class HomeFeature(TimeStampedModel):
    name = models.CharField(max_length=100)
    caption = models.CharField(max_length=200)
    image = models.ImageField(upload_to='home/features/')
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.name


class GalleryImage(TimeStampedModel):
    title = models.CharField(max_length=120, blank=True)
    image = models.ImageField(upload_to='home/gallery/')
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.title or f'Gallery image {self.pk}'


class CouncilMember(TimeStampedModel):
    STUDENT = 'student'
    MANAGEMENT = 'management'
    COUNCIL_CHOICES = [
        (STUDENT, 'Student Council'),
        (MANAGEMENT, 'Management Council'),
    ]

    name = models.CharField(max_length=100)
    position = models.CharField(max_length=100)
    bio = models.TextField(blank=True)
    council_type = models.CharField(max_length=20, choices=COUNCIL_CHOICES, default=STUDENT)
    image = models.ImageField(upload_to='council/', blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name






from django.db import models
from django.utils import timezone
from datetime import datetime

class Event(TimeStampedModel):
    CULTURAL = 'cultural'
    SCIENTIFIC = 'scientific'
    SPORTS = 'sports'

    CATEGORY_CHOICES = [
        (CULTURAL, 'Cultural'),
        (SCIENTIFIC, 'Scientific'),
        (SPORTS, 'Sports'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default=CULTURAL)

    date = models.DateField()
    time = models.TimeField(null=True, blank=True)

    registration_end = models.DateTimeField(null=True, blank=True)

    venue = models.CharField(max_length=150, blank=True)
    image = models.ImageField(upload_to='events/', blank=True)
    drive_link = models.URLField(blank=True)
    allow_student_registration = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    @property
    def can_register(self):
        if not self.allow_student_registration:
            return False

        if self.registration_end:
            return timezone.now() <= self.registration_end

        return False

    class Meta:
        ordering = ['order', 'date', 'time']

    def __str__(self):
        return self.title
        





class EventPhoto(models.Model):
    event = models.ForeignKey(
        Event,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="photos"
    )
    photo = models.ImageField(upload_to="event_photos/")
    drive_link = models.URLField(blank=True)

    def __str__(self):
        return str(self.event)

class Club(TimeStampedModel):
    name = models.CharField(max_length=120)
    color = models.CharField(
        max_length=20,
        default='#ffcc00',
        help_text='Use a hex color such as #ffcc00.',
    )
    image = models.ImageField(upload_to='clubs/', blank=True)
    founder = models.CharField(max_length=120)
    guide = models.CharField(max_length=120, blank=True)
    foundation_members = models.TextField(blank=True)
    rules_and_regulations = models.TextField(blank=True)
    description = models.TextField(blank=True)
    starting_date = models.DateField()
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Update(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    image = models.ImageField(upload_to='updates/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class EventRegistration(TimeStampedModel):
    SOLO = 'solo'
    TEAM = 'team'
    PERFORMANCE_CHOICES = [
        (SOLO, 'Solo'),
        (TEAM, 'Team'),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    full_name = models.CharField(max_length=160)
    registration_number = models.CharField(max_length=50)
    batch_name = models.CharField(max_length=80)
    performance_type = models.CharField(max_length=10, choices=PERFORMANCE_CHOICES, default=SOLO)
    team_size = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.registration_number} - {self.event.title}'


class EventRegistrationMember(TimeStampedModel):
    registration = models.ForeignKey(
        EventRegistration,
        on_delete=models.CASCADE,
        related_name='members',
    )
    full_name = models.CharField(max_length=160)
    registration_number = models.CharField(max_length=50)
    batch_name = models.CharField(max_length=80)
    order = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ['order', 'full_name']
        constraints = [
            models.UniqueConstraint(
                fields=['registration', 'registration_number'],
                name='unique_member_regnum_per_submission',
            ),
        ]

    def __str__(self):
        return f'{self.registration_number} - {self.registration.event.title}'


class Prize(TimeStampedModel):
    CULTURAL = 'cultural'
    SPORTS = 'sports'
    SCIENTIFIC = 'scientific'
    CATEGORY_CHOICES = [
        (CULTURAL, 'Cultural'),
        (SPORTS, 'Sports'),
        (SCIENTIFIC, 'Scientific'),
    ]

    name = models.CharField(max_length=100)
    achievement = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default=CULTURAL)
    date = models.DateField(null=True, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', '-date', 'name']

    def __str__(self):
        return self.name


class PrizeCompetition(TimeStampedModel):
    CULTURAL = 'cultural'
    SPORTS = 'sports'
    SCIENTIFIC = 'scientific'
    CATEGORY_CHOICES = [
        (CULTURAL, 'Cultural'),
        (SPORTS, 'Sports'),
        (SCIENTIFIC, 'Scientific'),
    ]

    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default=CULTURAL)
    title = models.CharField(max_length=160)
    poster = models.ImageField(upload_to='prizes/posters/', blank=True)
    announcement_date = models.DateField()
    announcement_time = models.TimeField(null=True, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['category', 'order', '-announcement_date', 'title']

    def __str__(self):
        return self.title


class PrizeWinner(TimeStampedModel):
    SOLO = 'solo'
    TEAM = 'team'
    WINNER_TYPE_CHOICES = [
        (SOLO, 'Solo winner'),
        (TEAM, 'Batch/Team winner'),
    ]

    competition = models.ForeignKey(PrizeCompetition, on_delete=models.CASCADE, related_name='winners')
    prize_label = models.CharField(max_length=50, help_text='Example: 1st Prize, 2nd Prize, Best Performer')
    winner_type = models.CharField(max_length=10, choices=WINNER_TYPE_CHOICES, default=SOLO)
    winner_name = models.CharField(max_length=140, help_text='Student name, batch name, or team name')
    batch_or_team = models.CharField(max_length=120, blank=True, help_text='Example: Batch 2026 or Team Incendios')
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'prize_label']

    def __str__(self):
        return f'{self.prize_label}: {self.winner_name}'


class InfoCategory(TimeStampedModel):
    STYLE_CHOICES = [
        ('info-one', 'University Updates'),
        ('info-two', 'NSS Updates'),
        ('info-three', 'Hostel Updates'),
    ]

    title = models.CharField(max_length=100)
    subtitle = models.CharField(max_length=160, blank=True)
    style_class = models.CharField(max_length=20, choices=STYLE_CHOICES, default='info-one')
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'title']
        verbose_name_plural = 'Info categories'

    def __str__(self):
        return self.title


class InfoUpdate(TimeStampedModel):
    category = models.ForeignKey(InfoCategory, on_delete=models.CASCADE, related_name='updates')
    title = models.CharField(max_length=150)
    description = models.TextField()
    external_url = models.URLField(blank=True, help_text='Optional link to an outside website')
    pdf = models.FileField(upload_to='info/pdfs/', blank=True, help_text='Optional PDF upload')
    date = models.DateField(null=True, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', '-date', '-created_at']

    def __str__(self):
        return self.title


class ContactMessage(TimeStampedModel):
    name = models.CharField(max_length=100, blank=True)
    email = models.EmailField()
    message = models.TextField()
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Message from {self.email}'
