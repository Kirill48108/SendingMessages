from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = "Создаёт менеджера (is_staff=True). Используйте --superuser для суперпользователя."

    def add_arguments(self, parser):
        parser.add_argument("--username", type=str, help="Имя пользователя")
        parser.add_argument("--email", type=str, help="Email")
        parser.add_argument("--password", type=str, help="Пароль")
        parser.add_argument("--superuser", action="store_true", help="Создать суперпользователя")

    def handle(self, *args, **options):
        User = get_user_model()
        username = options.get("username") or input("Username: ").strip()
        email = options.get("email") or input("Email: ").strip()
        password = options.get("password") or input("Password: ").strip()
        make_superuser = options.get("superuser", False)

        if not username or not email or not password:
            raise CommandError("Необходимо указать username, email и password.")

        if User.objects.filter(username=username).exists():
            raise CommandError(f"Пользователь '{username}' уже существует.")

        if make_superuser:
            User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f"Суперпользователь '{username}' создан."))
            return

        user = User.objects.create_user(username=username, email=email, password=password)
        user.is_staff = True
        user.is_active = True
        user.save(update_fields=["is_staff", "is_active"])
        self.stdout.write(self.style.SUCCESS(f"Менеджер '{username}' создан (is_staff=True)."))


