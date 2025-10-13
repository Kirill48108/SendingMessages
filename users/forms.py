from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import PasswordResetForm
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.tokens import default_token_generator



class LoginAuthenticationForm(AuthenticationForm):
    """
    Стандартная форма входа, но поле 'username' подписано как 'Логин'.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Логин"
        self.fields["username"].widget.attrs.update({
            "placeholder": "Введите логин",
            "autofocus": True,
            "autocomplete": "username",
        })
        self.fields["password"].widget.attrs.update({
            "placeholder": "Пароль",
            "autocomplete": "current-password",
        })


class NamespacedPasswordResetForm(PasswordResetForm):
    def save(
        self,
        domain_override=None,
        subject_template_name="registration/password_reset_subject.txt",
        email_template_name="registration/password_reset_email_users.html",
        use_https=False,
        token_generator=default_token_generator,
        from_email=None,
        request=None,
        html_email_template_name=None,
        extra_email_context=None,
    ):
        email = self.cleaned_data["email"]
        if not domain_override:
            current_site = get_current_site(request)
            site_name = current_site.name
            domain = current_site.domain
        else:
            site_name = domain = domain_override

        protocol = "https" if use_https else "http"

        for user in self.get_users(email):
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            token = token_generator.make_token(user)
            reset_path = reverse(
                "users:password_reset_confirm",
                kwargs={"uidb64": uidb64, "token": token},
            )
            reset_url = request.build_absolute_uri(reset_path) if request else f"{protocol}://{domain}{reset_path}"

            context = {
                "email": user.email,
                "domain": domain,
                "site_name": site_name,
                "uid": uidb64,
                "user": user,
                "token": token,
                "protocol": protocol,
                "reset_url": reset_url,
            }
            if extra_email_context:
                context.update(extra_email_context)

            self.send_mail(
                subject_template_name,
                email_template_name,
                context,
                from_email,
                user.email,
                html_email_template_name=html_email_template_name,
            )
