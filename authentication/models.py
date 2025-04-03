from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    email = models.EmailField('email address', unique=True)
    telefone = models.CharField(max_length=15)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def save(self, *args, **kwargs):
        if not self.username:  # Se username estiver vazio
            self.username = self.email  # Usa email como username
        super().save(*args, **kwargs)