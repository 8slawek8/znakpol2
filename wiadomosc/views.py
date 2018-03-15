from django.shortcuts import render, redirect
from django import forms

from django.contrib import messages
from django.views.generic import ListView, DetailView, DeleteView, CreateView
from django.db.models import Q

from wiadomosc.models import Wiadomosc
from pracownik.models import Uzytkownik
from pracownik.views import LoginRequiredMixin

class WiadomoscIloscMixin:
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['nieprzeczytane'] = self.request.user.wiadomosc_set\
                .filter(odczytana=False).count()
        return context

class WiadomoscLDMixin(WiadomoscIloscMixin, LoginRequiredMixin):
    model = Wiadomosc

    def get_queryset(self, *args, **kwargs):
        user = self.request.user
        return super().get_queryset(*args, **kwargs)\
            .filter(Q(odbiorca_list=user) | Q(nadawca=user)).distinct()

class WiadomoscListView(WiadomoscLDMixin, ListView):
    def get_context_data(self, *args, **kwargs):
        user = self.request.user
        context = super().get_context_data(*args, **kwargs)
        context['object_list_odbiorcza'] = context['object_list'].filter(odbiorca_list=user)
        context['object_list_nadawcza'] = context['object_list'].filter(nadawca=user)
        return context

class WiadomoscDetailView(WiadomoscLDMixin, DetailView):
    def get(self, *args, **kwargs):
        self.object = self.get_object() 
        self.object.odczytana = True
        self.object.save()
        return super().get(*args, **kwargs)

class WiadomoscCreateView(WiadomoscIloscMixin, LoginRequiredMixin, CreateView):
    model = Wiadomosc
    fields = ['temat','tresc','odbiorca_list','zalacznik']
    template_name = 'default_form.html'
    success_url = '/wiadomosci/'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = Wiadomosc()
        kwargs['instance'].nadawca = self.request.user
        return kwargs

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        form.fields['odbiorca_list'].widget.attrs.update({'class' : 'form-control'})
        if self.request.user.klient:
            form.fields['odbiorca_list'].queryset = Uzytkownik.objects.filter(klient=False)
        return form

class WiadomoscOdpowiedzView(WiadomoscIloscMixin, LoginRequiredMixin, CreateView):
    model = Wiadomosc
    fields = ['tresc']
    template_name = 'default_form.html'

    def get_form_kwargs(self):
        self.success_url = '/wiadomosc/{}/'.format(self.kwargs['pk'])
        kwargs = super().get_form_kwargs()
        self.wiadomosc_stara = Wiadomosc.objects.get(pk=self.kwargs['pk'])
        kwargs['instance'] = Wiadomosc()
        kwargs['instance'].temat = 'RE: {}'.format(self.wiadomosc_stara.temat)
        kwargs['instance'].nadawca = self.request.user
        return kwargs

    def form_valid(self, form):
        self.object = form.save()
        self.object.odbiorca_list.add(Uzytkownik.objects.get(pk=self.wiadomosc_stara.nadawca_id))
        messages.success(self.request, 'Wiadomość została wysłana.')
        return super().form_valid(form)



class WiadomoscKontaktCreateView(WiadomoscIloscMixin, CreateView):
    model = Wiadomosc
    fields = ['tresc']
    template_name = 'default_form.html'
    success_url = '/'

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        form.fields['klient'] = forms.CharField(max_length=100)
        form.fields['email'] = forms.EmailField()
        return form

    def form_valid(self, form):
        d = form.cleaned_data
        form.instance.temat = 'Wiadomosc z formularza strony'
        form.instance.tresc = '{} <br> {} <br><em>{}</em>'.format(d['tresc'],d['klient'],d['email'])
        w = form.save()
        w.odbiorca_list.add(*Uzytkownik.objects.filter(pracownik__stanowisko__name='Kierownik działu projektów'))
        messages.success(self.request, 'Wiadomość została wysłana.')
        return redirect(self.success_url) 

class WiadomoscPromocjaCreateView(WiadomoscIloscMixin, CreateView):
    model = Wiadomosc
    fields = ['tresc']
    template_name = 'default_form.html'
    success_url = '/'

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        form.fields['zamowienie'] = forms.CharField(max_length=100)
        form.fields['email'] = forms.EmailField()
        del form.fields['tresc']
        return form

    def form_valid(self, form):
        d = form.cleaned_data
        form.instance.temat = 'Wiadomosc z formularza promocyjnego'
        form.instance.tresc = 'Zamówienie nr: {} prosi o promocję.<br> Email klienta: {}'.format(d['zamowienie'],d['email'])
        w = form.save()
        w.odbiorca_list.add(*Uzytkownik.objects.filter(pracownik__stanowisko__name='Kierownik działu projektów'))
        messages.success(self.request, 'Wiadomość została wysłana.')
        return redirect(self.success_url) 


class WiadomoscDeleteView(WiadomoscIloscMixin, LoginRequiredMixin, DeleteView):
    model = Wiadomosc
    template_name = 'default_confirm_delete.html'
    success_url = '/wiadomosci/'
