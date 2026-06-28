from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('info/',views.info,name='info'),
    path('council/', views.council, name='council'),
    path('mcouncil/',views.mcouncil,name='mcouncil'),
    path('events/', views.events, name='events'),
    path('event-registration/', views.event_registration, name='event_registration'),
    path('prizes/', views.prizes, name='prizes'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('clubs/',views.clubs,name='clubs'),
    path('export-excel/', views.export_excel, name='export_excel'),
]
