from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin as LoginDjango
from django.contrib.auth.models import Group as Stanowisko
from django.shortcuts import redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from pracownik.models import Uzytkownik, Pracownik

class RejestracjaView(CreateView): 
    model = Uzytkownik
    fields = ['username','first_name','last_name','email','telefon','adres']
    success_url = '/uzytkownicy/'
    template_name = 'rejestracja.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        if self.request.user.is_authenticated:
            context['nieprzeczytane'] = self.request.user.wiadomosc_set\
                    .filter(odczytana=False).count()
        return context
   
    def get_form(self, *args, **kwargs):
        form_class = self.get_form_class()
        def _clean(self):
            d = self.cleaned_data
            if not d.get('haslo') or d.get('haslo') != d.get('haslo_powtorz'):
                raise forms.ValidationError('Podane hasła nie są jednakowe.')
            if Uzytkownik.objects.filter(username=d.get('username')).exclude(pk=self.instance.id).exists():
                raise forms.ValidationError('Użytkownik o podanym loginie już istnieje. Podaj inny login.')
            return d
        form_class.clean = _clean
        form = super().get_form(form_class, *args, **kwargs)
        form.fields['username'].label = 'Login' 
        form.fields['haslo'] = forms.CharField(label='Hasło', widget=forms.PasswordInput)
        form.fields['haslo_powtorz'] = forms.CharField(label='Potwierdź hasło', widget=forms.PasswordInput)
        return form

    def form_valid(self, form):
        from wiadomosc.models import Wiadomosc
        haslo = form.cleaned_data.get('haslo')
        form.instance.klient = True
        form.instance.set_password(haslo)
        form.save()
        wiadomosc = Wiadomosc.objects.create(
            temat='Witamy w systemie',
            tresc=('Gorąco witamy w systemie ZnakPoL, życzmy udanych zakupów i miłej pracy'),
            nadawca=Uzytkownik.objects.get(username='adam'),
        )
        wiadomosc.odbiorca_list.add(form.instance)
        messages.success(self.request, 'Rejestracja przebiegła pomyślnie. Zaloguj się.')
        return redirect('/login/')

class LoginRequiredMixin(LoginDjango):
    login_url = '/login/'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['nieprzeczytane'] = self.request.user.wiadomosc_set\
                .filter(odczytana=False).count()
        return context

class SuperUserView:
    def dispatch(self, *args, **kwargs):
        if not self.request.user.is_superuser:
            messages.error(self.request, 'Brak uprawnień.')
            return redirect('/produkty/')
        return super().dispatch(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['nieprzeczytane'] = self.request.user.wiadomosc_set\
                .filter(odczytana=False).count()
        return context

class UzytkownikMixin(SuperUserView):
    model = Uzytkownik
    fields = ['username','first_name','last_name','email','telefon','adres','klient','is_superuser']
    success_url = '/uzytkownicy/'

class UzytkownikListView(LoginRequiredMixin, ListView):
    model = Uzytkownik

    def dispatch(self, *args, **kwargs):
        if hasattr(self.request.user, 'klient') and self.request.user.klient:
            messages.error(self.request, 'Brak uprawnień.')
            return redirect('/')
        return super().dispatch(*args, **kwargs)

class UzytkownikDetailView(LoginRequiredMixin, DetailView):
    model = Uzytkownik

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        if not self.request.user.is_superuser:
            return qs.filter(pk=self.request.user.id)
        return qs
    
class UzytkownikCreateView(UzytkownikMixin, CreateView): template_name = 'default_form.html'

class UzytkownikUpdateView(LoginRequiredMixin, UpdateView): 
    model = Uzytkownik
    fields = ['username','first_name','last_name','email','telefon','adres','klient','is_superuser']
    template_name = 'default_form.html'
    success_url = '/uzytkownicy/'

    def get_object(self, *args, **kwargs):
        obj = super().get_object(*args, **kwargs)
        if not self.request.user.is_superuser:
            self.object = obj = Uzytkownik.objects.get(pk=self.request.user.id)
        return obj
   
    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        form.fields['username'].label = 'Login'
        if not self.request.user.is_superuser:
            del form.fields['klient']
            del form.fields['is_superuser']
            self.success_url = '/uzytkownik/{}'.format(self.request.user.id)
        return form

class ZmienHasloView(LoginRequiredMixin, UpdateView): 
    model = Uzytkownik
    template_name = 'default_form.html'
    fields = ['password']
    
    def get(self, *args, **kwargs):
        messages.error(self.request, 'Uwaga! Zmiana hasła powoduje wylogowanie z systemu. Po zmianie wymagane jest ponowne zalogowanie')
        return super().get(*args, **kwargs)


    def get_object(self, *args, **kwargs):
        obj = super().get_object(*args, **kwargs)
        if not self.request.user.is_superuser:
            self.object = obj = Uzytkownik.objects.get(pk=self.request.user.id)
        return obj

    def get_form(self, *args, **kwargs):
        form_class = self.get_form_class()
        def _clean(self):
            d = self.cleaned_data
            if not d.get('haslo') or d.get('haslo') != d.get('haslo_powtorz'):
                raise forms.ValidationError('Podane hasła nie są jednakowe.')
            return d
        form_class.clean = _clean
        form = super().get_form(form_class, *args, **kwargs)
        form.fields['haslo'] = forms.CharField(label='Hasło', widget=forms.PasswordInput)
        form.fields['haslo_powtorz'] = forms.CharField(label='Potwierdź hasło', widget=forms.PasswordInput)
        del form.fields['password']
        return form

    def form_valid(self, form):
        haslo = form.cleaned_data.get('haslo')
        obj = Uzytkownik.objects.get(pk=form.instance.id)
        obj.set_password(haslo)
        obj.save()
        messages.success(self.request, 'Hasło zmienione pomyślnie')
        return self.request.GET('next') or redirect('/uzytkownicy/')


class UzytkownikDeleteView(UzytkownikMixin, DeleteView): template_name = 'default_confirm_delete.html'


class StanowiskoMixin(SuperUserView):
    model = Stanowisko
    fields = ['name']
    success_url = '/stanowiska/'

class StanowiskoListView(StanowiskoMixin, ListView): 
    model = Stanowisko
    template_name = 'pracownik/stanowisko_list.html'
class StanowiskoDetailView(StanowiskoMixin, DetailView): pass
class StanowiskoCreateView(StanowiskoMixin, CreateView): template_name = 'default_form.html'
class StanowiskoUpdateView(StanowiskoMixin, UpdateView): template_name = 'default_form.html'
class StanowiskoDeleteView(StanowiskoMixin, DeleteView): template_name = 'default_confirm_delete.html'


class PracownikMixin(SuperUserView):
    model = Pracownik
    fields = '__all__'
    success_url = '/uzytkownicy/'

class PracownikCreateView(PracownikMixin, CreateView): template_name = 'default_form.html'
class PracownikUpdateView(PracownikMixin, UpdateView): template_name = 'default_form.html'
class PracownikDeleteView(PracownikMixin, DeleteView): template_name = 'default_confirm_delete.html'
