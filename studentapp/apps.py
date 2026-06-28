from django.apps import AppConfig


class StudentappConfig(AppConfig):
    name = 'studentapp'

    def ready(self):
        import studentapp.signals
