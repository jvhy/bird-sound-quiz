from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password, password_validators_help_text_html


User = get_user_model()

class CustomUserCreationForm(forms.ModelForm):
    """
    A form for creating new users. Includes repeated password validation.
    """
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirm Password", widget=forms.PasswordInput, help_text=password_validators_help_text_html())

    class Meta:
        model = User
        fields = ("username",)

    def clean(self):
        """Validate password."""
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        username = cleaned_data.get("username")
        if password1 and username:
            self.instance.username = username  # set instance username so similarity validation works
            validate_password(password1, self.instance)
        return cleaned_data

    def clean_password2(self):
        """Check that passwords are equal."""
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match.")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user
