from django.core.management.base import BaseCommand
from django.utils import timezone
from sendingmessages.models import Mailing
from sendingmessages.services import send_mailing as send_mailing_service

class Command(BaseCommand):
    help = "Отправка всех активных рассылок, находящихся в окне времени."

    def handle(self, *args, **options):
        now = timezone.now()
        qs = Mailing.objects.filter(is_disabled=False, start_at__lte=now, end_at__gte=now)
        count_total = 0
        for mailing in qs:
            result = send_mailing_service(mailing)
            count_total += result.get("total", 0)
            # обновление статуса
            if mailing.status != Mailing.STATUS_RUNNING:
                mailing.status = Mailing.STATUS_RUNNING
                mailing.save(update_fields=["status"])
        self.stdout.write(self.style.SUCCESS(f"Готово. Обработано рассылок: {qs.count()}, всего писем: {count_total}"))
