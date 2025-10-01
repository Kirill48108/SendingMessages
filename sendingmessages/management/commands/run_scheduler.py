from django.core.management.base import BaseCommand
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from django_apscheduler.jobstores import DjangoJobStore, register_events, register_job
from django.utils import timezone
from sendingmessages.models import Mailing
from sendingmessages.services import send_mailing as send_mailing_service

class Command(BaseCommand):
    help = "Запускает планировщик отправки рассылок."

    def handle(self, *args, **options):
        scheduler = BlockingScheduler(timezone=str(timezone.get_current_timezone()))
        scheduler.add_jobstore(DjangoJobStore(), "default")

        @register_job(scheduler, CronTrigger(minute="*"), id="send_mailings_periodic", replace_existing=True)
        def job_send_mailings():
            now = timezone.now()
            qs = Mailing.objects.filter(is_disabled=False, start_at__lte=now, end_at__gte=now)
            for mailing in qs:
                send_mailing_service(mailing)
                if mailing.status != Mailing.STATUS_RUNNING:
                    mailing.status = Mailing.STATUS_RUNNING
                    mailing.save(update_fields=["status"])

        register_events(scheduler)
        self.stdout.write(self.style.SUCCESS("Планировщик запущен. Нажмите Ctrl+C для остановки."))
        try:
            scheduler.start()
        except KeyboardInterrupt:
            scheduler.shutdown()
            self.stdout.write(self.style.WARNING("Планировщик остановлен"))

