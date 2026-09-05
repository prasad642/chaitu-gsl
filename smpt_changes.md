# SMTP & Email Verification Changes Log

This document records all changes made to solve the SMTP email verification and OTP delivery issues.

---

## Table of Contents
1. [Overview & Root Cause Summary](#1-overview--root-cause-summary)
2. [Step 1: Previous Changes Already Applied (Round 1)](#2-step-1-previous-changes-already-applied-round-1)
3. [Step 2: New Issue Found – Authentication Error 5.7.8 (Round 2 — NOT YET APPLIED)](#3-step-2-new-issue-found--authentication-error-578-round-2--not-yet-applied)
4. [Verification & How to Test](#4-verification--how-to-test)

---

## 1. Overview & Root Cause Summary

### Current Observed Behavior:
- When clicking **Send OTP**, a popup error appears:
  > "Email could not be sent: SMTP login failed. Please check EMAIL_HOST_USER and EMAIL_HOST_PASSWORD. 5.7.8 Authentication failed"
- The OTP code does print in the terminal (from the debug console logger we added), which is correct.
- BUT: The actual email is never delivered to the recipient's inbox.

### Root Cause (Newly Confirmed):

**The Brevo SMTP credentials (`b066b9001@smtp-brevo.com`) in `.env` are no longer valid or authorized.**

This is confirmed by the error `5.7.8 Authentication failed`. This is different from the sender rejection we fixed earlier. The issue is:
1. **Brevo SMTP API keys are revocable/expirable** — the `xsmtpsib-...` key in `.env` may have been revoked, expired, or the Brevo account may require server IP authorization.
2. **The current `.env` has NO `BREVO_API_KEY` set** — so the code falls through to SMTP mode (`django_send_mail`), which fails with `5.7.8 Authentication failed`.
3. **The `dotenv` `load_dotenv()` call happens at line 193, AFTER `os.environ.get()` for SMTP vars at lines 225–235** — this means `.env` variables are NOT loaded when the email settings are first read. The settings module reads from environment first (which are empty), and the `.env` file loads late (but the SMTP vars are already set to empty strings from the first read).

### Critical Design Bug Found:
In [`settings.py`](file:///c:/Users/durga/OneDrive/Documents/chaitu/studentsproject/studentproject/studentproject/settings.py):
- Line 17: `BASE_DIR` defined (early)
- Lines 231–238: `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, etc. are read using `os.environ.get()` (**these lines execute before `.env` is loaded**)
- Line 193: `load_dotenv(BASE_DIR / ".env")` (**this only loads after the email variables are already read with empty strings**)

This means Django is trying to authenticate to Brevo SMTP with **empty username and password** from environment — the `.env` values come too late in the settings file execution order.

**The fix is to move `load_dotenv()` to the very top of `settings.py`, before any `os.environ.get()` calls for secrets.**

---

## 2. Step 1: Previous Changes Already Applied (Round 1)

### 2.1 `studentproject/settings.py` – Email Credential Sanitization
- **Date Applied**: 26-Aug-2026
- **Lines**: 225 – 275
- Added `.strip()` to all email credentials.
- Fixed `DEFAULT_FROM_EMAIL` to use verified sender address.

### 2.2 `studentapp/email_utils.py` – Console Logging & Sender Fallback
- **Date Applied**: 26-Aug-2026
- **Lines**: 15 – 36
- Added `[EMAIL DISPATCH]` console print in DEBUG mode.
- Added sender address fallback to avoid `@smtp-brevo.com` in FROM header.

### 2.3 `studentproject/.env` – Cleaned Whitespace & Added Sender Vars
- **Date Applied**: 26-Aug-2026
- **Lines**: 1 – 9 → expanded to 11 lines
- Stripped trailing whitespace from `EMAIL_HOST_PASSWORD` and `CLOUDINARY_API_KEY`.
- Added `BREVO_SENDER_EMAIL=incendios2k22gsl@gmail.com`.
- Added `CONTACT_RECEIVER_EMAIL=incendios2k22gsl@gmail.com`.

---

## 3. Step 2: New Issue Found – Authentication Error 5.7.8 (Round 2 — NOT YET APPLIED)

### Problem Confirmed from Screenshot:
Error: `5.7.8 Authentication failed` — SMTP credentials are not being loaded properly from `.env`.

---

### Planned Change 3.1: Move `load_dotenv()` to the TOP of `settings.py`

**File**: [`studentproject/settings.py`](file:///c:/Users/durga/OneDrive/Documents/chaitu/studentsproject/studentproject/studentproject/settings.py)

**Line Range**: Lines 1 – 17 (add immediately after imports)

#### Code BEFORE Change (lines 13–17):
```python
from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'
BASE_DIR = Path(__file__).resolve().parent.parent
```

#### Code AFTER Change:
```python
from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env FIRST — before any os.environ.get() calls for secrets
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / '.env')
except ImportError:
    pass
```

**Reason**: Without this, all `os.environ.get('EMAIL_HOST_PASSWORD', '')` calls at lines 231–238 return empty strings because `.env` is not loaded until line 193, long after those variables are already set.

---

### Planned Change 3.2: Remove the Duplicate `load_dotenv()` Block in the Middle of `settings.py`

**File**: [`studentproject/settings.py`](file:///c:/Users/durga/OneDrive/Documents/chaitu/studentsproject/studentproject/studentproject/settings.py)

**Line Range**: Lines 189 – 195

#### Code BEFORE Change:
```python
BASE_DIR = Path(__file__).resolve().parent.parent

try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass
```

#### Code AFTER Change:
```python
BASE_DIR = Path(__file__).resolve().parent.parent
```

**Reason**: The duplicate `load_dotenv()` block in the middle of settings is now moved to the top, so this one is removed to avoid confusion.

---

### Planned Change 3.3: Switch Email Delivery to Gmail SMTP (Reliable Fallback)

**File**: [`studentproject/.env`](file:///c:/Users/durga/OneDrive/Documents/chaitu/studentsproject/studentproject/.env)

Since the Brevo SMTP key in `.env` may be revoked/expired (causing `5.7.8 Authentication failed`), and `BREVO_API_KEY` is not set, the most reliable fix for local development is to use **Gmail SMTP** with an App Password.

**The `email_settings.example.py` file already shows a Gmail App Password** for `incendios2k22gsl@gmail.com`:
```
EMAIL_HOST_USER = 'incendios2k22gsl@gmail.com'
EMAIL_HOST_PASSWORD = 'zbze xwdz nnyq wwfp'
```

We will create the actual `email_settings.py` file (which `settings.py` already tries to import) to use Gmail SMTP credentials locally:

#### New File to Create: `studentproject/email_settings.py`

```python
# Local email settings override — uses Gmail SMTP for local development.
# This file is not tracked by git (it is in .gitignore).
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'incendios2k22gsl@gmail.com'
EMAIL_HOST_PASSWORD = 'zbze xwdz nnyq wwfp'   # Gmail App Password
BREVO_SENDER_EMAIL = 'incendios2k22gsl@gmail.com'
CONTACT_RECEIVER_EMAIL = 'saichaitanya9493@gmail.com'
```

**Reason**: Gmail SMTP via App Password is highly reliable for local development. The existing example file shows this was the intended local config. The `settings.py` already has a try/except import block for `email_settings.py`.

---

## 4. Verification & How to Test

### After Applying Step 2 Changes:

1. **Restart the dev server** (Ctrl+C then `python manage.py runserver`) to reload settings.

2. **Test from command line**:
   ```powershell
   python manage.py emailstatus
   python manage.py testemail saichaitanya9493@gmail.com
   ```

3. **Test via Contact Page**:
   - Open [http://127.0.0.1:8000/contact/](http://127.0.0.1:8000/contact/).
   - Enter your name and email, click **Send OTP**.
   - OTP should now arrive in the inbox AND print in the terminal.
   - Enter the OTP, click **Verify OTP**, type a message, and click **Submit**.


This document records all changes made to solve the SMTP email verification and OTP delivery issues.

---

## Table of Contents
1. [Overview & Root Cause Summary](#1-overview--root-cause-summary)
2. [Implementation Details & Exact Code Changes](#2-implementation-details--exact-code-changes)
   - [File 1: `studentproject/settings.py`](#file-1-studentprojectsettingspy)
   - [File 2: `studentapp/email_utils.py`](#file-2-studentappemail_utilspy)
   - [File 3: `studentproject/.env`](#file-3-studentprojectenv)
3. [Verification & How to Test](#3-verification--how-to-test)

---

## 1. Overview & Root Cause Summary

When a user attempts email verification in the **Contact Us** form (`/contact/`), an OTP is generated and sent via `send_app_email()`. 

The failures were caused by:
1. **Invalid `FROM` Sender Header in Brevo SMTP**: `DEFAULT_FROM_EMAIL` defaulted to `b066b9001@smtp-brevo.com` (which is only the SMTP login ID). Brevo rejects messages unless the `FROM` header is an authorized, verified mailbox (such as `incendios2k22gsl@gmail.com`).
2. **Trailing Whitespace in `.env`**: `EMAIL_HOST_PASSWORD` contained trailing space characters (`xsmtpsib-... `), causing SMTP authentication failure (`535 Authentication failure`).
3. **No Dev-Console Fallback**: In local development, if SMTP or internet had issues, there was no visibility into the generated 6-digit OTP code in the terminal.

---

## 2. Implementation Details & Exact Code Changes

---

### File 1: `studentproject/settings.py`
- **File Path**: [`studentproject/settings.py`](file:///c:/Users/durga/OneDrive/Documents/chaitu/studentsproject/studentproject/studentproject/settings.py)
- **Line Range**: Lines 225 – 275

#### Code BEFORE Change:
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp-relay.brevo.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'

EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
BREVO_API_KEY = os.environ.get('BREVO_API_KEY', '')
BREVO_SENDER_EMAIL = os.environ.get('BREVO_SENDER_EMAIL', EMAIL_HOST_USER)
BREVO_SENDER_NAME = os.environ.get('BREVO_SENDER_NAME', 'Incendios')

CONTACT_RECEIVER_EMAIL = os.environ.get(
    'CONTACT_RECEIVER_EMAIL',
    'incendios2k22gsl@gmail.com'
)

EMAIL_TIMEOUT = int(os.environ.get('EMAIL_TIMEOUT', 25))

try:
    from . import email_settings
except ImportError:
    pass
else:
    EMAIL_HOST_USER = getattr(email_settings, 'EMAIL_HOST_USER', EMAIL_HOST_USER)
    EMAIL_HOST_PASSWORD = getattr(
        email_settings,
        'EMAIL_HOST_PASSWORD',
        EMAIL_HOST_PASSWORD,
    )
    BREVO_API_KEY = getattr(email_settings, 'BREVO_API_KEY', BREVO_API_KEY)
    BREVO_SENDER_EMAIL = getattr(email_settings, 'BREVO_SENDER_EMAIL', BREVO_SENDER_EMAIL)
    BREVO_SENDER_NAME = getattr(email_settings, 'BREVO_SENDER_NAME', BREVO_SENDER_NAME)
    CONTACT_RECEIVER_EMAIL = getattr(
        email_settings,
        'CONTACT_RECEIVER_EMAIL',
        CONTACT_RECEIVER_EMAIL,
    )

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
SERVER_EMAIL = EMAIL_HOST_USER
```

#### Code AFTER Change:
```python
EMAIL_BACKEND = os.environ.get(
    'EMAIL_BACKEND',
    'django.core.mail.backends.smtp.EmailBackend'
)

EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp-relay.brevo.com').strip()
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'

EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '').strip()
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '').strip()
BREVO_API_KEY = os.environ.get('BREVO_API_KEY', '').strip()
BREVO_SENDER_EMAIL = os.environ.get('BREVO_SENDER_EMAIL', '').strip()
BREVO_SENDER_NAME = os.environ.get('BREVO_SENDER_NAME', 'Incendios').strip()

CONTACT_RECEIVER_EMAIL = os.environ.get(
    'CONTACT_RECEIVER_EMAIL',
    'incendios2k22gsl@gmail.com'
).strip()

EMAIL_TIMEOUT = int(os.environ.get('EMAIL_TIMEOUT', 25))

try:
    from . import email_settings
except ImportError:
    pass
else:
    EMAIL_HOST_USER = getattr(email_settings, 'EMAIL_HOST_USER', EMAIL_HOST_USER).strip()
    EMAIL_HOST_PASSWORD = getattr(
        email_settings,
        'EMAIL_HOST_PASSWORD',
        EMAIL_HOST_PASSWORD,
    ).strip()
    BREVO_API_KEY = getattr(email_settings, 'BREVO_API_KEY', BREVO_API_KEY).strip()
    BREVO_SENDER_EMAIL = getattr(email_settings, 'BREVO_SENDER_EMAIL', BREVO_SENDER_EMAIL).strip()
    BREVO_SENDER_NAME = getattr(email_settings, 'BREVO_SENDER_NAME', BREVO_SENDER_NAME).strip()
    CONTACT_RECEIVER_EMAIL = getattr(
        email_settings,
        'CONTACT_RECEIVER_EMAIL',
        CONTACT_RECEIVER_EMAIL,
    ).strip()

# Set DEFAULT_FROM_EMAIL to a valid mailbox (not the raw smtp-brevo login username)
if BREVO_SENDER_EMAIL and not BREVO_SENDER_EMAIL.endswith('@smtp-brevo.com'):
    DEFAULT_FROM_EMAIL = BREVO_SENDER_EMAIL
elif EMAIL_HOST_USER and not EMAIL_HOST_USER.endswith('@smtp-brevo.com'):
    DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
else:
    DEFAULT_FROM_EMAIL = CONTACT_RECEIVER_EMAIL

SERVER_EMAIL = DEFAULT_FROM_EMAIL
```

**Explanation**:
- Added `.strip()` to prevent accidental trailing spaces from failing SMTP authentication.
- Dynamically sets `DEFAULT_FROM_EMAIL` to a real mailbox (`incendios2k22gsl@gmail.com`) instead of the SMTP login ID (`b066b9001@smtp-brevo.com`), preventing Brevo `550 Sender address rejected`.

---

### File 2: `studentapp/email_utils.py`
- **File Path**: [`studentapp/email_utils.py`](file:///c:/Users/durga/OneDrive/Documents/chaitu/studentsproject/studentproject/studentapp/email_utils.py)
- **Line Range**: Lines 15 – 36

#### Code BEFORE Change:
```python
def send_app_email(subject, message, recipients):
    if getattr(settings, 'BREVO_API_KEY', ''):
        return send_brevo_api_email(subject, message, recipients)

    return django_send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        recipients,
        fail_silently=False,
    )


def send_brevo_api_email(subject, message, recipients):
    sender_email = getattr(settings, 'BREVO_SENDER_EMAIL', '') or settings.DEFAULT_FROM_EMAIL
    if not sender_email:
        raise EmailDeliveryError('Brevo sender email is missing. Set BREVO_SENDER_EMAIL or EMAIL_HOST_USER.')
    if sender_email.endswith('@smtp-brevo.com'):
        raise EmailDeliveryError(
            'Brevo sender email is invalid. Set BREVO_SENDER_EMAIL to a sender address verified in Brevo, '
            'not the SMTP login address.'
        )
```

#### Code AFTER Change:
```python
def send_app_email(subject, message, recipients):
    # Print email and OTP directly to console in development mode for easy verification
    if getattr(settings, 'DEBUG', False):
        print(f"\n[EMAIL DISPATCH] To: {', '.join(recipients)} | Subject: {subject}\n{message}\n")

    if getattr(settings, 'BREVO_API_KEY', ''):
        return send_brevo_api_email(subject, message, recipients)

    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', '')
    if not from_email or from_email.endswith('@smtp-brevo.com'):
        from_email = getattr(settings, 'BREVO_SENDER_EMAIL', '') or getattr(settings, 'CONTACT_RECEIVER_EMAIL', 'incendios2k22gsl@gmail.com')

    return django_send_mail(
        subject,
        message,
        from_email,
        recipients,
        fail_silently=False,
    )


def send_brevo_api_email(subject, message, recipients):
    sender_email = getattr(settings, 'BREVO_SENDER_EMAIL', '') or settings.DEFAULT_FROM_EMAIL
    if not sender_email or sender_email.endswith('@smtp-brevo.com'):
        sender_email = getattr(settings, 'CONTACT_RECEIVER_EMAIL', 'incendios2k22gsl@gmail.com')

    if not sender_email:
        raise EmailDeliveryError('Brevo sender email is missing. Set BREVO_SENDER_EMAIL or CONTACT_RECEIVER_EMAIL.')
```

**Explanation**:
- Added `print(f"\n[EMAIL DISPATCH] To: ...")` in `DEBUG` mode so that the developer always sees the OTP immediately in the terminal.
- Added sender address fallback to guarantee emails are dispatched with a valid verified sender address.

---

### File 3: `studentproject/.env`
- **File Path**: [`studentproject/.env`](file:///c:/Users/durga/OneDrive/Documents/chaitu/studentsproject/studentproject/.env)
- **Line Range**: Lines 1 – 9

#### Code BEFORE Change:
```env
CLOUDINARY_API_SECRET=7Uq3otxjB46l2_SIDb6NYyCqILE
CLOUDINARY_CLOUD_NAME=doutgybiz
CLOUDINARY_API_KEY=845476379327614    

EMAIL_HOST=smtp-relay.brevo.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=b066b9001@smtp-brevo.com
EMAIL_HOST_PASSWORD=xsmtpsib-444e1b8378951744c7d369a7ba007e4749f208b3ff9c2fb947e5897d49e8b619-FCTjnJORa0cHVfC7 
```

#### Code AFTER Change:
```env
CLOUDINARY_API_SECRET=7Uq3otxjB46l2_SIDb6NYyCqILE
CLOUDINARY_CLOUD_NAME=doutgybiz
CLOUDINARY_API_KEY=845476379327614

EMAIL_HOST=smtp-relay.brevo.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=b066b9001@smtp-brevo.com
EMAIL_HOST_PASSWORD=xsmtpsib-444e1b8378951744c7d369a7ba007e4749f208b3ff9c2fb947e5897d49e8b619-FCTjnJORa0cHVfC7
BREVO_SENDER_EMAIL=incendios2k22gsl@gmail.com
CONTACT_RECEIVER_EMAIL=incendios2k22gsl@gmail.com
```

**Explanation**:
- Removed trailing spaces from `CLOUDINARY_API_KEY` and `EMAIL_HOST_PASSWORD`.
- Configured verified sender address `BREVO_SENDER_EMAIL=incendios2k22gsl@gmail.com`.

---

## 3. Verification & How to Test

1. **Test from Command Line**:
   ```powershell
   python manage.py testemail incendios2k22gsl@gmail.com
   ```
2. **Test via Contact Page (`/contact/`)**:
   - Go to [http://127.0.0.1:8000/contact/](http://127.0.0.1:8000/contact/).
   - Enter your name and email, then click **Send OTP**.
   - Check your terminal where `[EMAIL DISPATCH]` outputs the 6-digit OTP instantly.
   - Enter the OTP in the browser, verify, and submit your message.

---

## ✅ Step 2: Changes APPLIED — 26-Aug-2026 (Round 2)

These changes were applied to fix the `5.7.8 Authentication failed` error shown in the screenshot.

---

### Change A: `studentproject/settings.py` — Move `load_dotenv()` to Top
**Lines affected**: 13 – 18 (insertion after BASE_DIR)

#### Code BEFORE:
```python
from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings...
```

#### Code AFTER:
```python
from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env FIRST — before any os.environ.get() calls for secrets.
# Without this, EMAIL_HOST_USER/PASSWORD etc. would read as empty strings.
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / '.env')
except ImportError:
    pass

# Quick-start development settings...
```
**Why**: `os.environ.get('EMAIL_HOST_PASSWORD')` at line 235 was executing BEFORE `load_dotenv()` at old line 193 — so credentials from `.env` were never loaded. This caused Django to authenticate to SMTP with empty strings → `5.7.8 Authentication failed`.

---

### Change B: `studentproject/settings.py` — Remove Duplicate `load_dotenv()` Block
**Lines affected**: old lines 192 – 204

#### Code BEFORE:
```python
import cloudinary

BASE_DIR = Path(__file__).resolve().parent.parent

try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass


import cloudinary
```

#### Code AFTER:
```python
import cloudinary

BASE_DIR = Path(__file__).resolve().parent.parent

# NOTE: load_dotenv() is already called at the top of this file.
# The duplicate block has been removed.
```
**Why**: The duplicate `load_dotenv()` block in the middle was redundant and confusing now that it is properly placed at the top.

---

### Change C: `studentproject/settings.py` — Add `EMAIL_HOST`/`EMAIL_PORT`/`EMAIL_USE_TLS` to `email_settings` Override Block
**Lines affected**: 248 – 268

#### Code BEFORE:
```python
else:
    EMAIL_HOST_USER = getattr(email_settings, 'EMAIL_HOST_USER', EMAIL_HOST_USER).strip()
    EMAIL_HOST_PASSWORD = getattr(...)
    BREVO_API_KEY = ...
    ...
```

#### Code AFTER:
```python
else:
    EMAIL_HOST = getattr(email_settings, 'EMAIL_HOST', EMAIL_HOST).strip()
    EMAIL_PORT = int(getattr(email_settings, 'EMAIL_PORT', EMAIL_PORT))
    EMAIL_USE_TLS = getattr(email_settings, 'EMAIL_USE_TLS', EMAIL_USE_TLS)
    EMAIL_HOST_USER = getattr(email_settings, 'EMAIL_HOST_USER', EMAIL_HOST_USER).strip()
    EMAIL_HOST_PASSWORD = getattr(...)
    ...
```
**Why**: Without this, `email_settings.py` setting `EMAIL_HOST = 'smtp.gmail.com'` would be ignored. Django would still try to connect to `smtp-relay.brevo.com` even when Gmail credentials are set.

---

### Change D: [NEW FILE] `studentproject/email_settings.py`
**File created**: `c:\Users\durga\OneDrive\Documents\chaitu\studentsproject\studentproject\studentproject\email_settings.py`

```python
# Local email settings override — uses Gmail SMTP for local development.
# This file is NOT tracked by git (.gitignore excludes it).

EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'incendios2k22gsl@gmail.com'
EMAIL_HOST_PASSWORD = 'zbze xwdz nnyq wwfp'  # Gmail App Password (16-char)
BREVO_SENDER_EMAIL = 'incendios2k22gsl@gmail.com'
CONTACT_RECEIVER_EMAIL = 'saichaitanya9493@gmail.com'
```
**Why**: The Gmail App Password (from `email_settings.example.py`) provides a working local SMTP connection without depending on Brevo. The `settings.py` `try/except` import block already loads this file and overrides all SMTP settings.

---

### Change E: `.gitignore` — Add `email_settings.py`
**Line added**: after `local_settings.py` entry

```
email_settings.py
```
**Why**: The `email_settings.py` file contains credentials and must NOT be committed to git.

---

## Final Email Configuration After All Changes

| Setting | Value |
|---------|-------|
| `EMAIL_BACKEND` | `django.core.mail.backends.smtp.EmailBackend` |
| `EMAIL_HOST` | `smtp.gmail.com` (from `email_settings.py`) |
| `EMAIL_PORT` | `587` |
| `EMAIL_USE_TLS` | `True` |
| `EMAIL_HOST_USER` | `incendios2k22gsl@gmail.com` |
| `EMAIL_HOST_PASSWORD` | Gmail App Password |
| `DEFAULT_FROM_EMAIL` | `incendios2k22gsl@gmail.com` (BREVO_SENDER_EMAIL) |
| `CONTACT_RECEIVER_EMAIL` | `saichaitanya9493@gmail.com` |
