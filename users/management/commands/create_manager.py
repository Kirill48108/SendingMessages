from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from users.models import UserProfile
import getpass

class Command(BaseCommand):
    help = "Создать менеджера (пользователь с ролью manager)"

    def handle(self, *args, **options):
        username = input("Логин: ").strip()
        email = input("Email: ").strip()

        if User.objects.filter(username=username).exists():
            raise CommandError("Пользователь с таким логином уже существует.")

        while True:
            pwd1 = getpass.getpass("Пароль: ")
            pwd2 = getpass.getpass("Повторите пароль: ")
            if pwd1 != pwd2:
                self.stderr.write(self.style.ERROR("Пароли не совпадают, попробуйте снова."))
                continue
            if not pwd1:
                self.stderr.write(self.style.ERROR("Пароль не может быть пустым."))
                continue
            break

        user = User.objects.create_user(username=username, email=email, password=pwd1, is_active=True)
        UserProfile.objects.create(user=user, role=UserProfile.ROLE_MANAGER, is_blocked=False)

        self.stdout.write(self.style.SUCCESS(f"Менеджер '{username}' создан."))



