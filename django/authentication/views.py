from django.shortcuts import render
from django.urls import reverse
from django.http import HttpResponseRedirect
from .forms import RegisterForm

def index(request):
   return HttpResponseRedirect(reverse('login'))

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                
                return render(request, 'authentication/register.html', {
                    'form': RegisterForm(),  # Formulário limpo
                    'success_message': 'Cadastro realizado com sucesso! Você já pode fazer login.',
                })
            except Exception as e:
                return render(request, 'authentication/register.html', {
                    'form': form,
                    'error_message': f'Ocorreu um erro: {str(e)}',
                })
    else:
        form = RegisterForm()
    
    return render(request, 'authentication/register.html', {
        'form': form,
    })

def login(request):
   return render(request, 'authentication/login.html')