from django.contrib import admin
from django.contrib import messages
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group, User
from django.db import models
from django.template.response import TemplateResponse
from django.utils import timezone

from .models import (
    Club,
    ContactMessage,
    CouncilMember,
    Event,
    EventRegistration,
    EventRegistrationMember,
    GalleryImage,
    HomeFeature,
    HomeSlide,
    InfoCategory,
    InfoUpdate,
    PrizeCompetition,
    PrizeWinner,
    Update,
    Batch,
    Competition,
    Score,
    EventPhoto,

)

admin.site.site_header = 'Incendios Admin'
admin.site.site_title = 'Incendios Admin'
admin.site.index_title = 'Website Updates'


FIXED_INFO_CATEGORIES = [
    ('University Updates', 'info-one', 0),
    ('NSS Updates', 'info-two', 1),
    ('Hostel Updates', 'info-three', 2),
]


def ensure_fixed_info_categories():
    for title, style_class, order in FIXED_INFO_CATEGORIES:
        category = (
            InfoCategory.objects.filter(title=title).first()
            or InfoCategory.objects.filter(style_class=style_class).first()
        )

        if category is None:
            InfoCategory.objects.create(
                title=title,
                subtitle='',
                style_class=style_class,
                order=order,
                is_active=True,
            )
            continue

        updates = {
            'title': title,
            'subtitle': '',
            'style_class': style_class,
            'order': order,
            'is_active': True,
        }
        for field_name, value in updates.items():
            setattr(category, field_name, value)
        category.save()


class SingleAdminUserAdmin(UserAdmin):
    def has_add_permission(self, request):
        return not User.objects.filter(is_staff=True).exists()

    def save_model(self, request, obj, form, change):
        obj.is_staff = True
        obj.is_superuser = True
        super().save_model(request, obj, form, change)


class HomeSlideAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'is_active', 'updated_at')
    list_editable = ('order', 'is_active')
    search_fields = ('title',)


class HomeFeatureAdmin(admin.ModelAdmin):
    list_display = ('name', 'caption', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    search_fields = ('name', 'caption')


class GalleryImageAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'is_active', 'updated_at')
    list_editable = ('order', 'is_active')
    search_fields = ('title',)


class CouncilMemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'position', 'council_type', 'order', 'is_active')
    list_filter = ('council_type', 'is_active')
    list_editable = ('order', 'is_active')
    search_fields = ('name', 'position', 'bio')


class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'date', 'time', 'venue', 'drive_link', 'allow_student_registration', 'order', 'is_active')
    list_filter = ('category', 'allow_student_registration', 'is_active', 'date')
    list_editable = ('allow_student_registration', 'order', 'is_active')
    search_fields = ('title', 'description', 'venue', 'drive_link')


class EventPhotoAdmin(admin.ModelAdmin):
    list_display = ('event', 'photo', 'drive_link')
    list_filter = ('event__category',)
    search_fields = ('event__title', 'drive_link')
    autocomplete_fields = ()


class ClubAdmin(admin.ModelAdmin):
    list_display = ('name', 'founder', 'guide', 'starting_date', 'color', 'order', 'is_active')
    list_filter = ('is_active', 'starting_date')
    list_editable = ('order', 'is_active')
    search_fields = ('name', 'founder', 'guide', 'foundation_members', 'rules_and_regulations', 'description')


class PrizeWinnerInline(admin.TabularInline):
    model = PrizeWinner
    extra = 1
    fields = ('prize_label', 'winner_type', 'winner_name', 'batch_or_team', 'order', 'is_active')


class PrizeCompetitionAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'announcement_date', 'announcement_time', 'order', 'is_active')
    list_filter = ('category', 'is_active', 'announcement_date')
    list_editable = ('order', 'is_active')
    search_fields = ('title',)
    inlines = [PrizeWinnerInline]


class PrizeWinnerAdmin(admin.ModelAdmin):
    list_display = ('prize_label', 'winner_name', 'winner_type', 'competition', 'order', 'is_active')
    list_filter = ('winner_type', 'is_active', 'competition__category')
    list_editable = ('order', 'is_active')
    search_fields = ('prize_label', 'winner_name', 'batch_or_team', 'competition__title')


class InfoUpdateInline(admin.TabularInline):
    model = InfoUpdate
    extra = 1
    fields = ('title', 'description', 'external_url', 'pdf', 'date', 'order', 'is_active')


class InfoUpdateAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'date', 'external_url', 'pdf', 'order', 'is_active')
    list_filter = ('category', 'is_active', 'date')
    list_editable = ('order', 'is_active')
    search_fields = ('title', 'description', 'external_url')
    autocomplete_fields = ()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'category':
            ensure_fixed_info_categories()
            kwargs['queryset'] = InfoCategory.objects.filter(
                title__in=[title for title, _style_class, _order in FIXED_INFO_CATEGORIES],
                is_active=True,
            ).order_by('order', 'title')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('email', 'name', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    list_editable = ('is_read',)
    search_fields = ('name', 'email', 'message')
    readonly_fields = ('name', 'email', 'message', 'created_at', 'updated_at')

    def has_add_permission(self, request):
        return False


class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'registration_number', 'batch_name', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('full_name', 'registration_number', 'batch_name', 'event__title')
    readonly_fields = ('event', 'full_name', 'registration_number', 'batch_name', 'created_at', 'updated_at')
    change_list_template = 'admin/studentapp/eventregistration/change_list.html'

    def has_add_permission(self, request):
        return False

    def changelist_view(self, request, extra_context=None):
        today = timezone.localdate()
        selectable_events = Event.objects.filter(
            (
                models.Q(allow_student_registration=True, is_active=True, date__gte=today)
                | models.Q(registrations__isnull=False)
            )
        ).distinct().order_by('date', 'title')
        selected_event_id = request.GET.get('event_id', '').strip()
        selected_event = None
        registration_rows = []

        if request.method == 'POST':
            delete_member_id = request.POST.get('delete_member_id', '').strip()
            if delete_member_id.isdigit():
                member = EventRegistrationMember.objects.filter(pk=int(delete_member_id)).select_related('registration').first()
                if member is not None:
                    registration = member.registration
                    member.delete()
                    remaining = registration.members.count()
                    if remaining == 0:
                        registration.delete()
                    elif registration.team_size != remaining:
                        registration.team_size = remaining
                        registration.save(update_fields=['team_size', 'updated_at'])
                    messages.success(request, 'Registration entry deleted successfully.')
                else:
                    messages.error(request, 'Registration entry not found.')

        if selected_event_id:
            selected_event = selectable_events.filter(pk=selected_event_id).first()
            if selected_event is not None:
                registrations = EventRegistration.objects.filter(
                    event=selected_event
                ).prefetch_related('members').order_by('created_at', 'full_name')
                for registration in registrations:
                    members = list(registration.members.all())
                    if members:
                        for member in members:
                            registration_rows.append({
                                'member_id': member.id,
                                'full_name': member.full_name,
                                'registration_number': member.registration_number,
                                'batch_name': member.batch_name,
                            })
                    else:
                        registration_rows.append({
                            'member_id': '',
                            'full_name': registration.full_name,
                            'registration_number': registration.registration_number,
                            'batch_name': registration.batch_name,
                        })

        context = {
            **self.admin_site.each_context(request),
            'opts': self.model._meta,
            'allowed_events': selectable_events,
            'selected_event': selected_event,
            'registration_rows': registration_rows,
            'title': 'Event registrations',
        }
        if extra_context:
            context.update(extra_context)
        return TemplateResponse(request, self.change_list_template, context)


admin.site.unregister(User)
admin.site.unregister(Group)
admin.site.register(User, SingleAdminUserAdmin)
admin.site.register(HomeSlide, HomeSlideAdmin)
admin.site.register(HomeFeature, HomeFeatureAdmin)
admin.site.register(GalleryImage, GalleryImageAdmin)
admin.site.register(CouncilMember, CouncilMemberAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(EventPhoto, EventPhotoAdmin)
admin.site.register(Club, ClubAdmin)
admin.site.register(EventRegistration, EventRegistrationAdmin)
admin.site.register(PrizeCompetition, PrizeCompetitionAdmin)
admin.site.register(PrizeWinner, PrizeWinnerAdmin)
admin.site.register(InfoUpdate, InfoUpdateAdmin)
admin.site.register(ContactMessage, ContactMessageAdmin)


class UpdateAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at')
    search_fields = ('title', 'content')


admin.site.register(Update, UpdateAdmin)
from .models import Batch, Competition, Score

admin.site.register(Batch)
admin.site.register(Competition)
admin.site.register(Score)
