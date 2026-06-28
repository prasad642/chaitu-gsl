import os
import webbrowser
from threading import Timer
from wsgiref.simple_server import make_server
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "studentproject.settings")

def open_browser():
    webbrowser.open("http://127.0.0.1:8000")

if __name__ == "__main__":
    application = get_wsgi_application()
    Timer(1.5, open_browser).start()
    with make_server("127.0.0.1", 8000, application) as server:
        server.serve_forever()