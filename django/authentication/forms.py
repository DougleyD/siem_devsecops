from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django import forms
from .models import CustomUser

class RegisterForm(UserCreationForm):
    nome = forms.CharField(
        label='', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome completo'})
    )
    
    email = forms.EmailField(
        label='', widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'E-mail'})
    )

    telefone = forms.CharField(
        label='', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Telefone'})
    )
        
    password1 = forms.CharField(
        label='', widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Senha'})
    )

    password2 = forms.CharField(
        label='', widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirmar senha'})
    )

    class Meta:
        model = CustomUser
        fields = ['nome', 'email', 'telefone', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._errors = None  # Vamos controlar os erros manualmente

    def is_valid(self):
        # Sobrescreve is_valid para implementar validação sequencial
        self._errors = forms.utils.ErrorDict()
        self.cleaned_data = {}
        
        # Ordem de validação estrita
        validation_sequence = [
            self._validate_nome,
            self._validate_email,
            self._validate_telefone,
            self._validate_passwords
        ]
        
        for validation_step in validation_sequence:
            if not validation_step():
                return False  # Interrompe na primeira falha
        
        return len(self._errors) == 0


    def _validate_nome(self):
        nome = self.data.get('nome')
        if not nome:
            self._errors['nome'] = self.error_class(["O nome é obrigatório."])
            return False
        
        if len(nome.split()) < 2:
            self._errors['nome'] = self.error_class(["Por favor, insira seu nome completo."])
            return False
        
        self.cleaned_data['nome'] = nome
        return True

    def _validate_email(self):
        if 'nome' not in self.cleaned_data:  # Só valida se o nome estiver ok
            return False
            
        email = self.data.get('email')
        if not email:
            self._errors['email'] = self.error_class(["O e-mail é obrigatório."])
            return False
            
        if CustomUser.objects.filter(email=email).exists():
            self._errors['email'] = self.error_class(["Este e-mail já está cadastrado."])
            return False
            
        self.cleaned_data['email'] = email
        return True

    def _validate_telefone(self):
        if 'email' not in self.cleaned_data:  # Só valida se o email estiver ok
            return False
            
        telefone = self.data.get('telefone')
        if not telefone:
            self._errors['telefone'] = self.error_class(["O telefone é obrigatório."])
            return False
            
        if len(''.join(filter(str.isdigit, telefone))) < 10:
            self._errors['telefone'] = self.error_class(["Telefone inválido. Digite DDD + número."])
            return False
            
        self.cleaned_data['telefone'] = telefone
        return True

    def _validate_passwords(self):
        if 'telefone' not in self.cleaned_data:  # Só valida se o telefone estiver ok
            return False
            
        password1 = self.data.get('password1')
        password2 = self.data.get('password2')
        
        if not password1:
            self._errors['password1'] = self.error_class(["A senha é obrigatória."])
            return False
            
        if len(password1) < 8:
            self._errors['password1'] = self.error_class(["A senha deve ter pelo menos 8 caracteres."])
            return False
            
        if password1 != password2:
            self._errors['password2'] = self.error_class(["As senhas não coincidem."])
            return False
            
        self.cleaned_data['password1'] = password1
        self.cleaned_data['password2'] = password2
        return True
    
    def save(self, commit=True):
        user = super().save(commit=False)

        full_name = self.cleaned_data['nome'].split(' ', 1)

        user.first_name = full_name[0]
        user.last_name = full_name[1] if len(full_name) > 1 else ''
        user.email = self.cleaned_data['email']
        user.telefone = self.cleaned_data['telefone']
        
        if commit:
            user.save()
        return user