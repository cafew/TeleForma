from optparse import make_option
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.tokens import default_token_generator
from django.template.defaultfilters import slugify
from django.template.loader import render_to_string
from django.core.mail import send_mail, mail_admins
from django.utils import translation
from telemeta.models import *
from telemeta.util.unaccent import unaccent
from teleforma.models import *
from teleforma.views import *
import logging
import datetime


class Command(BaseCommand):
    help = """Manually increase seminar revision time"""

    def handle(self, *args, **kwargs):
        users = User.objects.all()
        for user in users:
            auditor = user.auditor.all()
            professor = user.professor.all()
            if auditor and not professor and user.is_active and user.email:
                auditor = auditor[0]
                context = {}
                seminars = auditor.seminars.all()
                for seminar in seminars:
                    revisions = SeminarRevision.objects.filter(user=user, seminar=seminar)
                    if revisions:
                        progress = seminar_progress(user, seminar)
                        validated = seminar_validated(user, seminar)
                        timer = get_seminar_timer(user, seminar)
                        bonus = datetime.timedelta(seconds=seminar.duration.as_seconds())
                        delta = timer - bonus
                        if delta.total_seconds() < 0 and progress == 100 and validated:
                            if not revisions[0].date_modified:
                                if len(revisions) > 1:
                                    revision = revisions[1]
                                    if revision.date_modified:
                                        revision.date_modified = revision.date_modified + bonus
                                    else:
                                        revision.date_modified = revision.date + bonus
                                else:
                                    revision = revisions[0]
                                    revision.date_modified = revision.date + bonus
                            else:
                                revision = revisions[0]
                                revision.date_modified = revision.date_modified + bonus
                            revision.save()