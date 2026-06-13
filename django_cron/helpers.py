from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext as _
from django.template.defaultfilters import pluralize


def humanize_duration(duration):
    """
    Returns a humanized string representing time difference

    For example: 2 days 1 hour 25 minutes 10 seconds
    """
    days = duration.days
    hours = int(duration.seconds / 3600)
    minutes = int(duration.seconds % 3600 / 60)
    seconds = int(duration.seconds % 3600 % 60)

    parts = []
    if days > 0:
        parts.append(u'%s %s' % (days, pluralize(days, _('day,days'))))

    if hours > 0:
        parts.append(u'%s %s' % (hours, pluralize(hours, _('hour,hours'))))

    if minutes > 0:
        parts.append(u'%s %s' % (minutes, pluralize(minutes, _('minute,minutes'))))

    if seconds > 0:
        parts.append(u'%s %s' % (seconds, pluralize(seconds, _('second,seconds'))))

    return ', '.join(parts) if len(parts) != 0 else _('< 1 second')


def get_class(kls):
    """
    Converts a string to a class.
    Courtesy: http://stackoverflow.com/questions/452969/does-python-have-an-equivalent-to-java-class-forname/452981#452981
    """
    parts = kls.split('.')

    if len(parts) == 1:
        raise ImportError("'{0}'' is not a valid import path".format(kls))

    module = ".".join(parts[:-1])
    m = __import__(module)
    for comp in parts[1:]:
        m = getattr(m, comp)
    return m


def get_current_time():
    """
    Returns the current time in the project's configured timezone.

    When ``USE_TZ=True``, returns a timezone-aware datetime in the active
    timezone (``settings.TIME_ZONE`` or per-request override).
    When ``USE_TZ=False``, returns a naive datetime in local time.
    """
    now = timezone.now()
    if timezone.is_naive(now):
        return now
    return timezone.localtime(now)


def normalize_datetime(dt):
    """
    Ensures *dt* matches the project's timezone-awareness setting so that
    it can be safely compared with values produced by :func:`get_current_time`.

    * ``USE_TZ=True``  → always returns an aware datetime.
      Naive datetimes (e.g. from legacy log rows written before timezone
      support was enabled) are interpreted as belonging to the current
      timezone.
    * ``USE_TZ=False`` → always returns a naive datetime.
      Aware datetimes are converted to naive local time first.
    """
    if dt is None:
        return None

    use_tz = getattr(settings, 'USE_TZ', False)

    if use_tz:
        if timezone.is_naive(dt):
            return timezone.make_aware(dt, timezone.get_current_timezone())
        return dt
    else:
        if timezone.is_aware(dt):
            return timezone.make_naive(dt, timezone.get_current_timezone())
        return dt
