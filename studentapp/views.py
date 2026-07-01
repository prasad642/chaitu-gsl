from django.conf import settings
from django.db import IntegrityError
from django.db import transaction
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.shortcuts import redirect, render
from django.utils import timezone
from pathlib import Path
from random import SystemRandom
from smtplib import SMTPAuthenticationError, SMTPException
import socket
import time
import re
import secrets

from .models import (
    ContactMessage,
    CouncilMember,
    Club,
    Event,
    EventRegistration,
    EventRegistrationMember,
    GalleryImage,
    HomeFeature,
    HomeSlide,
    InfoCategory,
    PrizeCompetition,
    Update,
    EventPhoto,
)



# views.py

from django.shortcuts import get_object_or_404, render


def event_detail(request, pk):
    event = get_object_or_404(Event, pk=pk)
    

    return render(
        request,
        "students/events.html",
        {"event": event},
    )


from django.shortcuts import render
from .models import Batch, Competition, Score
from collections import defaultdict

def results_view(request):
    batches = Batch.objects.all()
    competitions = Competition.objects.all()
    scores = Score.objects.all()

    # Table data: {batch_id: {comp_id: score}}
    table_data = defaultdict(dict)

    for score in scores:
        table_data[score.batch.id][score.competition.id] = score.score

    # Batch totals
    batch_totals = {}
    for batch in batches:
        total = sum(table_data[batch.id].values())
        batch_totals[batch.id] = total

    # Highest total
    highest_total = max(batch_totals.values()) if batch_totals else 0

    # Ranking
    sorted_batches = sorted(batch_totals.items(), key=lambda x: x[1], reverse=True)
    rankings = {}
    rank = 1
    for batch_id, total in sorted_batches:
        rankings[batch_id] = rank
        rank += 1

    # Highest score per competition
    highest_scores = {}
    for comp in competitions:
        comp_scores = [table_data[b.id].get(comp.id, 0) for b in batches]
        highest_scores[comp.id] = max(comp_scores) if comp_scores else 0

    context = {
        'batches': batches,
        'competitions': competitions,
        'table_data': dict(table_data),
        'batch_totals': batch_totals,
        'highest_scores': highest_scores,
        'highest_total': highest_total,
        'rankings': rankings,
    }
    return render(request, 'students/events.html', context)



from django.http import HttpResponse
from openpyxl import Workbook
from .models import Batch, Competition, Score


def export_excel(request):
    wb = Workbook()
    ws = wb.active
    ws.title = "Scores"

    batches = Batch.objects.all()
    competitions = Competition.objects.all()
    scores = Score.objects.all()

    # Prepare data
    table_data = defaultdict(dict)
    for s in scores:
        table_data[s.batch.id][s.competition.id] = s.score

    # Header
    headers = ["Batch"]
    headers += [comp.name for comp in competitions]
    headers += ["Total"]

    ws.append(headers)

    # Rows
    for batch in batches:
        row = [batch.name]
        total = 0

        for comp in competitions:
            score = table_data[batch.id].get(comp.id, 0)
            row.append(score)
            total += score

        row.append(total)
        ws.append(row)

    # Response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=score_table.xlsx'

    wb.save(response)
    return response







from collections import defaultdict
from django.shortcuts import render
from .models import Batch, Competition, Score






REGISTRATION_PATTERN = re.compile(r'^(22|23|24|25|26)M102014(\d{3})$')

def is_valid_registration_number(registration_number):
    match = REGISTRATION_PATTERN.fullmatch(registration_number)
    if not match:
        return False
    last_three = int(match.group(2))
    return 0 <= last_three <= 250


def is_valid_email(email):
    try:
        validate_email(email)
    except ValidationError:
        return False
    return True


def email_settings_error():
    missing = []
    if not settings.EMAIL_HOST_USER:
        missing.append('sender email')
    if not settings.EMAIL_HOST_PASSWORD:
        missing.append('SMTP password/API key')

    if not missing:
        return ''

    return 'Email is not configured: missing ' + ' and '.join(missing) + '.'


def clear_contact_otp_session(request):
    for key in [
        'contact_otp',
        'contact_otp_time',
        'contact_otp_email',
        'contact_name',
        'contact_otp_verified',
        'contact_otp_verified_at',
    ]:
        request.session.pop(key, None)
    request.session.modified = True


def email_delivery_error_message(exc):
    message = str(exc)
    if isinstance(exc, (TimeoutError, socket.timeout)):
        return (
            'Email could not be sent: SMTP connection timed out. '
            'Check EMAIL_HOST, EMAIL_PORT, EMAIL_USE_TLS, and whether your hosting provider can reach the SMTP server.'
        )
    if isinstance(exc, SMTPAuthenticationError):
        details = ''
        if len(exc.args) > 1:
            details = exc.args[1].decode(errors='ignore') if isinstance(exc.args[1], bytes) else str(exc.args[1])
        if 'Unauthorized IP address' in details or 'Unauthorized IP address' in message:
            return (
                'Email could not be sent: Brevo rejected this server IP address. '
                'Add this server IP to Brevo authorized IPs, or switch EMAIL_HOST settings to an approved SMTP provider.'
            )
        detail_text = details or message
        return f'Email could not be sent: SMTP login failed. Please check EMAIL_HOST_USER and EMAIL_HOST_PASSWORD. {detail_text}'
    if isinstance(exc, SMTPException):
        return f'Email could not be sent: SMTP error: {message}'
    return f'Email could not be sent: {message}'


def home(request):
    images_dir = Path(__file__).resolve().parent / 'static' / 'students' / 'images'
    second_carousel_static_images = [
        {
            'url': f"students/images/{image_file.name}",
            'title': image_file.stem.replace('-', ' ').title(),
            'is_static': True,
        }
        for image_file in sorted(images_dir.glob('homepage-second-carousel*'))
        if image_file.is_file()
    ]
    gallery_images = list(GalleryImage.objects.filter(is_active=True))
    second_carousel_images = [
        {
            'url': image.image.url,
            'title': image.title or 'Gallery image',
            'is_static': False,
        }
        for image in gallery_images
    ] + second_carousel_static_images
    context = {
        'top_slides': HomeSlide.objects.filter(is_active=True),
        'features': HomeFeature.objects.filter(is_active=True),
        'gallery_images': gallery_images,
        'second_carousel_images': second_carousel_images,
    }
    return render(request, 'students/home.html', context)


def council(request):
    council_members = CouncilMember.objects.filter(
        council_type=CouncilMember.STUDENT,
        is_active=True,
    )
    return render(request, 'students/council.html', {'council_members': council_members})


def mcouncil(request):
    management_members = CouncilMember.objects.filter(
        council_type=CouncilMember.MANAGEMENT,
        is_active=True,
    )
    return render(request, 'students/mcouncil.html', {'management_members': management_members})





def events(request):
    today = timezone.localdate()
    active_events = Event.objects.filter(is_active=True)
    cultural_events = list(active_events.filter(category=Event.CULTURAL))
    scientific_events = list(active_events.filter(category=Event.SCIENTIFIC))
    sports_events = list(active_events.filter(category=Event.SPORTS))

    
    today = timezone.localdate()

    active_events = Event.objects.filter(is_active=True)

    cultural_events = list(
        active_events.filter(category=Event.CULTURAL)
    )

    scientific_events = list(
        active_events.filter(category=Event.SCIENTIFIC)
    )

    sports_events = list(
        active_events.filter(category=Event.SPORTS)
    )

    event_sections = [
        {
            'title': 'CULTURAL EVENTS',
            'subtitle': 'Explore Heritage & Arts',
            'style': 'cultural-bg',
            'events': cultural_events,
        },
        {
            'title': 'SCIENTIFIC EVENTS',
            'subtitle': 'Innovation & Science',
            'style': 'scientific-bg',
            'events': scientific_events,
        },
        {
            'title': 'SPORTS EVENTS',
            'subtitle': 'Engage In Physical Activities',
            'style': 'sports-bg',
            'events': sports_events,
        },
    ]
                                        # -------------new table
    batches = Batch.objects.all()
    competitions = Competition.objects.all()
    scores = Score.objects.all()

    # Table data: {batch_id: {comp_id: score}}
    table_data = defaultdict(dict)

    for score in scores:
        table_data[score.batch.id][score.competition.id] = score.score

    # Batch totals
    batch_totals = {}
    for batch in batches:
        total = sum(table_data[batch.id].values())
        batch_totals[batch.id] = total

    # Highest total
    highest_total = max(batch_totals.values()) if batch_totals else 0

    # Ranking
    sorted_batches = sorted(batch_totals.items(), key=lambda x: x[1], reverse=True)
    rankings = {}
    rank = 1
    for batch_id, total in sorted_batches:
        rankings[batch_id] = rank
        rank += 1

    # Highest score per competition
    highest_scores = {}
    for comp in competitions:
        comp_scores = [table_data[b.id].get(comp.id, 0) for b in batches]
        highest_scores[comp.id] = max(comp_scores) if comp_scores else 0

    table_rows = []
    for batch in batches:
        scores_for_batch = []
        total = 0
        for comp in competitions:
            score = table_data[batch.id].get(comp.id, 0)
            scores_for_batch.append(score)
            total += score
        table_rows.append({
            'batch': batch,
            'scores': scores_for_batch,
            'total': total,
            'rank': rankings.get(batch.id, ''),
        })
    photos = EventPhoto.objects.select_related('event').exclude(photo='').order_by('-id')
    context = {
        'event_sections': event_sections,
        'today': today,
        'photos': photos,
        'batches': batches,
        'competitions': competitions,
        'table_data': dict(table_data),
        'table_rows': table_rows,
        'batch_totals': batch_totals,
        'highest_scores': highest_scores,
        'highest_total': highest_total,
        'rankings': rankings,
    }
    return render(request, 'students/events.html', context)







def clubs(request):
    clubs_list = Club.objects.filter(is_active=True)
    return render(request, 'students/clubs.html', {'clubs': clubs_list})

def event_registration(request):
    allowed_events = Event.objects.filter(
        is_active=True,
        allow_student_registration=True,
    )
    allowed_upcoming_events = allowed_events.filter(date__gte=timezone.localdate())

    selected_event_id = request.GET.get('event_id', '').strip()
    if selected_event_id and not allowed_events.filter(id=selected_event_id).exists():
        return redirect('events')

    if request.method == 'POST':
        selected_event_id = request.POST.get('event_id', '').strip()
        performance_type = request.POST.get('performance_type', EventRegistration.SOLO).strip().lower()
        team_count_raw = request.POST.get('team_count', '1').strip()
        member_names = [name.strip() for name in request.POST.getlist('member_full_name')]
        member_reg_numbers = [reg.strip() for reg in request.POST.getlist('member_registration_number')]
        member_batches = [batch.strip() for batch in request.POST.getlist('member_batch_name')]

        event = allowed_events.filter(id=selected_event_id).first()
        if not event:
            return render(request, 'students/event_registration.html', {
                'events': allowed_upcoming_events,
                'selected_event_id': selected_event_id,
                'popup_message': 'Registration failed',
                'error': 'Please choose a valid upcoming event.',
                'redirect_to_events': True,
            })

        if performance_type not in (EventRegistration.SOLO, EventRegistration.TEAM):
            return render(request, 'students/event_registration.html', {
                'events': allowed_upcoming_events,
                'selected_event_id': selected_event_id,
                'popup_message': 'Registration failed',
                'error': 'Please choose solo or team performance.',
                'redirect_to_events': True,
            })

        if performance_type == EventRegistration.SOLO:
            team_size = 1
        else:
            try:
                team_size = int(team_count_raw)
            except ValueError:
                team_size = 0
            if team_size < 2 or team_size > 15:
                return render(request, 'students/event_registration.html', {
                    'events': allowed_upcoming_events,
                    'selected_event_id': selected_event_id,
                    'popup_message': 'Registration failed',
                    'error': 'Team size must be between 2 and 15 students.',
                    'redirect_to_events': True,
                })

        if not (len(member_names) == len(member_reg_numbers) == len(member_batches) == team_size):
            return render(request, 'students/event_registration.html', {
                'events': allowed_upcoming_events,
                'selected_event_id': selected_event_id,
                'popup_message': 'Registration failed',
                'error': 'Please provide details for all students.',
                'redirect_to_events': True,
            })

        members = []
        for index in range(team_size):
            full_name = member_names[index]
            registration_number = member_reg_numbers[index]
            batch_name = member_batches[index]

            if not full_name or not registration_number or not batch_name:
                return render(request, 'students/event_registration.html', {
                    'events': allowed_upcoming_events,
                    'selected_event_id': selected_event_id,
                    'popup_message': 'Registration failed',
                    'error': 'Please fill all student details.',
                    'redirect_to_events': True,
                })

            if not is_valid_registration_number(registration_number):
                return render(request, 'students/event_registration.html', {
                    'events': allowed_upcoming_events,
                    'selected_event_id': selected_event_id,
                    'popup_message': 'Entered registration number is not found',
                    'error': 'Entered registration number is not found.',
                    'redirect_to_events': True,
                })

            members.append({
                'full_name': full_name,
                'registration_number': registration_number,
                'batch_name': batch_name,
                'order': index + 1,
            })

        if len({m['registration_number'] for m in members}) != len(members):
            return render(request, 'students/event_registration.html', {
                'events': allowed_upcoming_events,
                'selected_event_id': selected_event_id,
                'popup_message': 'Registration failed',
                'error': 'Duplicate registration numbers found in the same submission.',
                'redirect_to_events': True,
            })

        for member in members:
            existing_types = set(
                EventRegistrationMember.objects.filter(
                    registration__event=event,
                    registration_number=member['registration_number'],
                ).values_list('registration__performance_type', flat=True)
            )
            if not existing_types:
                continue
            # Allow solo registration even if the student already appears in a team.
            if performance_type == EventRegistration.SOLO and existing_types.issubset({EventRegistration.TEAM}):
                continue
            else:
                return render(request, 'students/event_registration.html', {
                    'events': allowed_upcoming_events,
                    'selected_event_id': selected_event_id,
                    'popup_message': 'Given registration number already registered',
                    'error': 'Given registration number already registered for this event.',
                    'redirect_to_events': True,
                })

        try:
            with transaction.atomic():
                registration = EventRegistration.objects.create(
                    event=event,
                    full_name=members[0]['full_name'],
                    registration_number=members[0]['registration_number'],
                    batch_name=members[0]['batch_name'],
                    performance_type=performance_type,
                    team_size=team_size,
                )
                EventRegistrationMember.objects.bulk_create([
                    EventRegistrationMember(registration=registration, **member)
                    for member in members
                ])
        except IntegrityError:
            return render(request, 'students/event_registration.html', {
                'events': allowed_upcoming_events,
                'selected_event_id': selected_event_id,
                'popup_message': 'Given registration number already registered',
                'error': 'Given registration number already registered for this event.',
                'redirect_to_events': True,
            })

        return render(request, 'students/event_registration.html', {
            'events': allowed_upcoming_events,
            'selected_event_id': '',
            'popup_message': 'Registration successfull',
            'success': True,
            'redirect_to_events': True,
        })

    return render(request, 'students/event_registration.html', {
        'events': allowed_upcoming_events,
        'selected_event_id': selected_event_id,
    })






def info(request):
    active_categories = {
        category.title: category
        for category in InfoCategory.objects.filter(is_active=True).prefetch_related('updates')
    }
    latest_updates = Update.objects.all()
    latest_update_photos = latest_updates.exclude(image='')
    info_sections = [
        {
            'title': 'University Updates',
            'banner': 'university-updates-banner.jpg',
            'category': active_categories.get('University Updates'),
        },
        {
            'title': 'NSS Updates',
            'banner': 'nss-updates-banner.jpg',
            'category': active_categories.get('NSS Updates'),
        },
        {
            'title': 'Hostel Updates',
            'banner': 'hostel-updates-banner.jpg',
            'category': active_categories.get('Hostel Updates'),
        },
    ]
    return render(request, 'students/info.html', {
        'info_sections': info_sections,
        'latest_updates': latest_updates,
        'latest_update_photos': latest_update_photos,
    })


def prizes(request):
    active_competitions = PrizeCompetition.objects.filter(is_active=True).prefetch_related('winners')
    context = {
        'cultural_competitions': active_competitions.filter(category=PrizeCompetition.CULTURAL),
        'sports_competitions': active_competitions.filter(category=PrizeCompetition.SPORTS),
        'scientific_competitions': active_competitions.filter(category=PrizeCompetition.SCIENTIFIC),
    }
    return render(request, 'students/prizes.html', context)


def about(request):
    return render(request, 'students/about.html')


def contact(request):

    if request.method == 'GET':
        # Pop flash before anything else — cleanup must not accidentally remove it
        flash = request.session.pop('contact_flash', None)

        # Discard flash older than 5 minutes (e.g. browser was closed mid-flow)
        if flash and (time.time() - flash.get('at', 0)) > 300:
            flash = None

        # ── Path A: Arriving from a successful OTP verification ─────────────
        # The flash carries the verified email/name. Generate a one-time submit
        # token so the form can be submitted — but any subsequent GET (refresh /
        # back button) will detect the token, clear it, and show a blank form.
        if flash and flash.get('type') == 'otp_verified':
            verified_email = flash.get('email', '')
            verified_name = flash.get('name', '')
            submit_token = secrets.token_hex(16)
            request.session['contact_submit_token'] = {
                'token': submit_token,
                'email': verified_email,
                'name': verified_name,
                'at': time.time(),
            }
            request.session.modified = True
            return render(request, 'students/contact.html', {
                'otp_email': verified_email,
                'contact_name': verified_name,
                'otp_verified': True,
                'otp_pending': False,
                'popup_message': flash.get('popup', ''),
                'submit_token': submit_token,
                'clear_local_storage': True,
            })

        # ── Path B: User refreshed or pressed back after verification ────────
        # A submit_token exists in session but no otp_verified flash was present,
        # meaning this is NOT the original post-verify page load.
        # Clear the token and show a completely blank form.
        if request.session.pop('contact_submit_token', None):
            request.session.modified = True
            return render(request, 'students/contact.html', {
                'clear_local_storage': True,
            })

        # ── Path C: Normal OTP-pending or fresh visit ─────────────────────────
        otp_email = request.session.get('contact_otp_email', '')
        otp_verified = False  # Verified state is never stored in session anymore
        contact_name = request.session.get('contact_name', '')
        saved_otp = request.session.get('contact_otp')
        otp_time = request.session.get('contact_otp_time', 0)

        is_otp_sent_flash = (flash and flash.get('type') == 'otp_sent')

        # If an OTP is active but this is NOT the immediate page load following
        # the 'send_otp' redirect (i.e. user refreshed the page manually while waiting),
        # wipe it all and show a blank form, per the requirement.
        if saved_otp and not is_otp_sent_flash:
            for key in ['contact_otp', 'contact_otp_time', 'contact_otp_email',
                        'contact_name', 'contact_otp_verified', 'contact_otp_verified_at']:
                request.session.pop(key, None)
            request.session.modified = True
            saved_otp = None
            otp_email = ''
            contact_name = ''

        # otp_pending: OTP was sent, not yet verified, and not expired
        otp_pending = (
            bool(saved_otp)
            and (time.time() - otp_time <= 120)
        )

        # If no active OTP and stale email lingers in session, clear it now
        if not otp_pending and otp_email:
            for key in ['contact_otp', 'contact_otp_time', 'contact_otp_email',
                        'contact_name', 'contact_otp_verified', 'contact_otp_verified_at']:
                request.session.pop(key, None)
            request.session.modified = True
            otp_email = ''
            contact_name = ''

        request.session.modified = True

        context = {
            'otp_email': otp_email,
            'contact_name': contact_name,
            'otp_verified': False,
            'otp_pending': otp_pending,
            'clear_local_storage': not otp_email,
        }

        if flash:
            context['popup_message'] = flash.get('popup', '')
            flash_type = flash.get('type', '')
            if flash_type == 'otp_sent':
                context['otp_sent'] = True
            elif flash_type == 'submitted':
                context['success'] = True
                context['clear_local_storage'] = True
                if flash.get('email_warning'):
                    context['email_warning'] = flash['email_warning']

        return render(request, 'students/contact.html', context)

    otp_email = request.session.get('contact_otp_email', '')
    otp_verified = request.session.get('contact_otp_verified', False)
    contact_name = request.session.get('contact_name', '')

    name = request.POST.get('name', '').strip()
    email = request.POST.get('email', '').strip()
    otp = request.POST.get('otp', '').strip()
    message = request.POST.get('message', '').strip()
    action = request.POST.get('action', '').strip()

    # ── STEP 1: Send OTP ────────────────────────────────────────────────────
    if action == 'send_otp':
        if not email or not is_valid_email(email):
            return render(request, 'students/contact.html', {
                'error': 'Please enter a valid email address.',
                'popup_message': 'Please enter a valid email address.',
                'otp_email': email,
                'contact_name': name,
                'otp_verified': False,
                'otp_pending': False,
            })

        settings_error = email_settings_error()
        if settings_error:
            return render(request, 'students/contact.html', {
                'error': settings_error,
                'popup_message': settings_error,
                'otp_email': email,
                'contact_name': name,
                'otp_verified': False,
                'otp_pending': False,
            })

        # Server-side rate limiting — JS-only cooldown is bypassable
        existing_otp_time = request.session.get('contact_otp_time', 0)
        existing_otp_email = request.session.get('contact_otp_email', '')
        if existing_otp_email == email and time.time() - existing_otp_time < 120:
            seconds_left = int(120 - (time.time() - existing_otp_time))
            return render(request, 'students/contact.html', {
                'error': f'Please wait {seconds_left} seconds before requesting a new OTP.',
                'popup_message': f'Please wait {seconds_left}s before requesting a new OTP.',
                'otp_email': email,
                'contact_name': name,
                'otp_verified': False,
                'otp_pending': True,
                'otp_sent': True,
            })

        generated_otp = f'{SystemRandom().randint(100000, 999999)}'
        request.session['contact_otp'] = generated_otp
        request.session['contact_otp_time'] = time.time()
        request.session['contact_otp_email'] = email
        request.session['contact_name'] = name
        request.session['contact_otp_verified'] = False
        request.session.modified = True

        try:
            send_mail(
                'Your Incendios contact OTP',
                f'Your OTP is {generated_otp}. Use this code to submit your message.',
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False,
            )
        except Exception as exc:
            error_message = email_delivery_error_message(exc)
            clear_contact_otp_session(request)
            return render(request, 'students/contact.html', {
                'error': error_message,
                'popup_message': error_message,
                'otp_email': email,
                'contact_name': name,
                'otp_verified': False,
                'otp_pending': False,
            })


        # PRG: flash then redirect — prevents refresh from re-sending the OTP email
        request.session['contact_flash'] = {'type': 'otp_sent', 'popup': 'OTP sent successfully', 'at': time.time()}
        request.session.modified = True
        return redirect('contact')

    # ── STEP 2 & 3: verify_otp / submit ─────────────────────────────────────
    saved_otp = request.session.get('contact_otp')
    saved_email = request.session.get('contact_otp_email')
    otp_time = request.session.get('contact_otp_time', 0)

    otp_pending = (
        bool(saved_otp)
        and not request.session.get('contact_otp_verified', False)
        and (time.time() - otp_time <= 120)
    )

    if action == 'verify_otp':
        # Edge case: verify clicked but no OTP was ever sent
        if not saved_otp:
            return render(request, 'students/contact.html', {
                'error': 'No OTP found. Please click "Send OTP" first.',
                'popup_message': 'No OTP found. Please send OTP first.',
                'otp_email': email or otp_email,
                'contact_name': name or contact_name,
                'otp_verified': False,
                'otp_pending': False,
            })

        if time.time() - otp_time > 120:
            # Clear ALL contact session data — not just OTP, but email and name too
            for key in ['contact_otp', 'contact_otp_time', 'contact_otp_email',
                        'contact_name', 'contact_otp_verified', 'contact_otp_verified_at']:
                request.session.pop(key, None)
            request.session.modified = True
            return render(request, 'students/contact.html', {
                'error': 'OTP has expired. Please click "Send OTP" to get a new one.',
                'popup_message': 'OTP expired. Please request a new one.',
                'otp_email': '',
                'contact_name': '',
                'otp_verified': False,
                'otp_pending': False,
                'clear_local_storage': True,
            })

        if not email or not is_valid_email(email) or not otp:
            return render(request, 'students/contact.html', {
                'error': 'Please enter a valid email and OTP.',
                'popup_message': 'OTP verification failed',
                'otp_email': email or otp_email,
                'contact_name': name or contact_name,
                'otp_verified': False,
                'otp_pending': otp_pending,
            })

        if email == saved_email and otp == saved_otp:
            # Verification success — store email+name in flash only, NOT in session
            # This ensures any subsequent GET (refresh/back) shows a blank form
            verified_email = email
            verified_name = name or contact_name
            for key in ['contact_otp', 'contact_otp_time', 'contact_otp_email',
                        'contact_name', 'contact_otp_verified', 'contact_otp_verified_at']:
                request.session.pop(key, None)
            request.session['contact_flash'] = {
                'type': 'otp_verified',
                'popup': 'OTP verified successfully',
                'email': verified_email,
                'name': verified_name,
                'at': time.time(),
            }
            request.session.modified = True
            return redirect('contact')

        request.session['contact_otp_verified'] = False
        request.session.modified = True
        return render(request, 'students/contact.html', {
            'error': 'Incorrect OTP. Please try again.',
            'popup_message': 'OTP verification failed',
            'otp_email': email or otp_email,
            'contact_name': name or contact_name,
            'otp_verified': False,
            'otp_pending': otp_pending,
        })

    # ── STEP 3: Submit message ───────────────────────────────────────────────
    submit_token_post = request.POST.get('submit_token', '').strip()
    token_data = request.session.get('contact_submit_token')

    # Validate the one-time submit token generated on the verification page load
    if (not token_data
            or not submit_token_post
            or token_data.get('token') != submit_token_post
            or token_data.get('email') != email
            or time.time() - token_data.get('at', 0) > 900):
        return render(request, 'students/contact.html', {
            'error': 'Your OTP session has expired. Please verify your email again to submit.',
            'popup_message': 'OTP session expired. Please verify again.',
            'otp_email': '',
            'contact_name': '',
            'otp_verified': False,
            'otp_pending': False,
            'clear_local_storage': True,
        })

    verified_name = token_data.get('name', '')

    if not message.strip():
        # Token is still valid — pass it back so user can correct and resubmit
        return render(request, 'students/contact.html', {
            'error': 'Please enter a message before submitting.',
            'popup_message': 'Please enter a message.',
            'otp_email': email,
            'contact_name': name or verified_name,
            'otp_verified': True,
            'otp_pending': False,
            'submit_token': submit_token_post,
        })

    use_name = name or verified_name
    # Consume the one-time token before creating the record
    request.session.pop('contact_submit_token', None)
    request.session.modified = True

    ContactMessage.objects.create(name=use_name, email=email, message=message)

    subject = f"New Contact Message from {use_name or email}"
    full_message = f"Name: {use_name or 'Not provided'}\nEmail: {email}\nMessage:\n{message}"

    try:
        send_mail(
            subject,
            full_message,
            settings.EMAIL_HOST_USER,
            [settings.CONTACT_RECEIVER_EMAIL],
            fail_silently=False,
        )
        request.session['contact_flash'] = {
            'type': 'submitted',
            'popup': 'Message submitted successfully',
            'at': time.time(),
        }
    except Exception:
        request.session['contact_flash'] = {
            'type': 'submitted',
            'popup': 'Message submitted successfully',
            'email_warning': 'Message saved. Email notification is not configured correctly yet.',
            'at': time.time(),
        }
    request.session.modified = True
    return redirect('contact')



import socket
from django.http import HttpResponse

def smtp_test(request):
    try:
        socket.create_connection(("smtp-relay.brevo.com", 587), timeout=10)
        return HttpResponse("SMTP reachable")
    except Exception as e:
        return HttpResponse(str(e))
