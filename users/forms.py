from django.contrib.auth.forms import AuthenticationForm

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
