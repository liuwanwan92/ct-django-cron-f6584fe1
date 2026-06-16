from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from django.db import transaction

from django_cron.backends.lock.base import DjangoCronJobLock
from django_cron.models import CronJobLock


class DatabaseLock(DjangoCronJobLock):
    """
    Locking cron jobs with database. Its good when you have not parallel run and want to make sure 2 jobs won't be
    fired at the same time - which may happened when job execution is longer that job interval.

    Supports stale-lock detection: if a process crashes without releasing the lock,
    another process can override it after the configured timeout elapses.
    """

    DEFAULT_LOCK_TIME = 24 * 60 * 60  # 24 hours, same as CacheLock

    def __init__(self, cron_class, *args, **kwargs):
        super().__init__(cron_class, *args, **kwargs)
        self.cron_class = cron_class
        self.timeout = self._get_timeout(cron_class)

    def _get_timeout(self, cron_class):
        # Check cron class first, then settings, then fall back to default.
        # Avoid eager evaluation of settings.DJANGO_CRON_LOCK_TIME (which may
        # not exist) by using hasattr checks instead of getattr with a default.
        if hasattr(cron_class, 'DJANGO_CRON_LOCK_TIME'):
            return cron_class.DJANGO_CRON_LOCK_TIME
        if hasattr(settings, 'DJANGO_CRON_LOCK_TIME'):
            return settings.DJANGO_CRON_LOCK_TIME
        return self.DEFAULT_LOCK_TIME

    @transaction.atomic
    def lock(self):
        lock, created = CronJobLock.objects.get_or_create(job_name=self.job_name)

        # Use select_for_update to prevent two transactions from both reading
        # locked=False and both acquiring the lock simultaneously.
        lock = CronJobLock.objects.select_for_update().get(pk=lock.pk)

        if lock.locked:
            # Check for stale lock: if locked_at is set and the timeout has
            # elapsed, the previous holder likely crashed — override it.
            if lock.locked_at is not None:
                elapsed = (timezone.now() - lock.locked_at).total_seconds()
                if elapsed > self.timeout:
                    lock.locked_at = timezone.now()
                    lock.save(update_fields=['locked_at'])
                    return True
            return False
        else:
            lock.locked = True
            lock.locked_at = timezone.now()
            lock.save(update_fields=['locked', 'locked_at'])
            return True

    @transaction.atomic
    def release(self):
        try:
            lock = CronJobLock.objects.select_for_update().get(
                job_name=self.job_name, locked=True
            )
        except CronJobLock.DoesNotExist:
            # Lock was already released (possibly by stale-lock override) — nothing to do.
            return
        lock.locked = False
        lock.locked_at = None
        lock.save(update_fields=['locked', 'locked_at'])
