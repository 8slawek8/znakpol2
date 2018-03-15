import datetime

from django import forms
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, \
        DeleteView, View

from pracownik.views import LoginRequiredMixin
from produkt.models import Produkt, Zamowienie, ZamowienieProdukt, ZamowienieStatus, \
        Magazyn, MagazynWydanie, MagazynPrzyjecie

User = get_user_model()


class ProduktFormFilter(forms.Form):
    nazwa = forms.CharField(required=False)
    marka = forms.CharField(required=False)
    opis = forms.CharField(required=False)
    cena_od = forms.DecimalField(required=False)
    cena_do = forms.DecimalField(required=False)
    sortuj = forms.MultipleChoiceField(required=False, 
            choices=[
                ('nazwa','nazwa A-Z'),
                ('-nazwa','nazwa Z-A'),
                ('marka','marka A-Z'),
                ('-marka','marka Z-A'),
                ('cena','cena rosnąco'),
                ('-cena','cena malejąco'),
                ])

class ProduktListView(ListView):
    model = Produkt

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        try:
            context['nieprzeczytane'] = self.request.user.wiadomosc_set\
                    .filter(odczytana=False).count()
        except AttributeError:
            pass
        return context

    def get(self, *args, **kwargs):
        qs = self.get_queryset()
        data = self.request.GET
        if not data:
            form = ProduktFormFilter()
        else:
            form = ProduktFormFilter(data)
            if data.get('nazwa'):
                qs = qs.filter(nazwa__icontains=data['nazwa'])
            if data.get('marka'):
                qs = qs.filter(marka__icontains=data['marka'])
            if data.get('opis'):
                qs = qs.filter(opis__icontains=data['opis'])
            if data.get('cena_od'):
                qs = qs.filter(cena__gte=data['cena_od'])
            if data.get('cena_do'):
                qs = qs.filter(cena__lte=data['cena_do'])
            if data.get('sortuj'):
                qs = qs.order_by(*data.getlist('sortuj'))
        self.object_list = qs
        context = self.get_context_data()
        context['form'] = form
        return self.render_to_response(context)



class ProduktDetailView(DetailView):
    model = Produkt

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        try:
            context['nieprzeczytane'] = self.request.user.wiadomosc_set\
                    .filter(odczytana=False).count()
        except AttributeError:
            pass
        return context

class ProduktMixin(LoginRequiredMixin):
    model = Produkt
    fields = '__all__'
    success_url = '/produkty/'

class ProduktCreateView(ProduktMixin, CreateView): pass
class ProduktUpdateView(ProduktMixin, UpdateView): pass
class ProduktDeleteView(ProduktMixin, DeleteView):
    template_name = 'default_confirm_delete.html'


class KoszykListView(ListView):
    model = Produkt
    template_name = 'produkt/koszyk_list.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        try:
            context['nieprzeczytane'] = self.request.user.wiadomosc_set\
                    .filter(odczytana=False).count()
        except AttributeError:
            pass
        return context

    def get(self, *args, **kwargs):
        if 'koszyk' not in self.request.session:
            messages.info(self.request, u'Koszyk zostanie utworzony po wybraniu produktu.')
            return redirect('/produkty/')
        return super().get(*args, **kwargs)

    def get_queryset(self, *args, **kwargs):
        koszyk = self.request.session['koszyk']['produkt_map']
        qs = self.model.objects.filter(pk__in=koszyk.keys())
        qs.suma = 0
        for i in qs:
            i.ilosc = koszyk[str(i.id)]
            i.wartosc = i.cena*i.ilosc
            qs.suma += i.wartosc
        return qs

class KoszykView(View):
    success_url = '/produkty/'

    def get(self, *args, **kwargs):
        self.request.session.modified = True
        pk = self.kwargs.get('pk')
        if 'koszyk' not in self.request.session and 'koszyk-dodaj' in self.kwargs:
            self.request.session['koszyk'] = {'ilosc': 0, 'produkt_map': {}}
        if 'koszyk-dodaj' in self.kwargs:
            produkt = Produkt.objects.get(pk=pk) 
            produkt_map = self.request.session['koszyk']['produkt_map']
            ilosc = (produkt_map[pk] if produkt_map.get(pk) else 0) + 1
            if not produkt.czy_dostepny(ilosc):
                messages.error(self.request, 'Aktualna ilość tego produktu została wyczerpana. Skontaktuj się z konsultantem.')
                return redirect(self.request.GET.get('next') or self.success_url, **kwargs)

            self.request.session['koszyk']['produkt_map'].setdefault(pk, 0)
            self.request.session['koszyk']['produkt_map'][pk] += 1
            self.request.session['koszyk']['ilosc'] +=1
        if 'koszyk-usun' in self.kwargs:
            try:
                self.request.session['koszyk']['produkt_map'][pk] -= 1
                if self.request.session['koszyk']['produkt_map'][pk] == 0:
                    del self.request.session['koszyk']['produkt_map'][pk]
                self.request.session['koszyk']['ilosc'] -=1
            except KeyError:
                pass

        if 'koszyk-usun-calosc' in self.kwargs:
            del self.request.session['koszyk']

        return redirect(self.request.GET.get('next') or self.success_url, **kwargs)

class ZamowienieFormFilter(forms.Form):
    nr_zamowienia = forms.CharField(required=False)
    klient = forms.CharField(required=False)
    adres = forms.CharField(required=False)
    wysylka_typ = forms.ChoiceField(required=False, label='Typ wysyłki', 
            choices=[('','')]+Zamowienie.WYSYLKA_CHOICES)
    sortuj = forms.MultipleChoiceField(required=False, 
            choices=[
                ('nr_zamowienia','nr_zamowienia A-Z'),
                ('-nr_zamowienia','nr_zamowienia Z-A'),
                ('wysylka_typ','wysylka_typ A-Z'),
                ('-wysylka_typ','wysylka_typ Z-A'),
                ('zrealizowane','zrealizowane=TAK'),
                ('-zrealizowane','zrealizowane=NIE'),
                ])

class ZamowienieListView(LoginRequiredMixin, ListView):
    model = Zamowienie

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        if self.request.user.klient:
            return qs.filter(user=self.request.user)
        return qs

    def get(self, *args, **kwargs):
        qs = self.get_queryset()
        data = self.request.GET
        if not data:
            form = ZamowienieFormFilter()
        else:
            form = ZamowienieFormFilter(data)
            if data.get('nr_zamowienia'):
                qs = qs.filter(nr_zamowienia__icontains=data['nr_zamowienia'])
            if data.get('klient'):
                qs = qs.filter(klient__icontains=data['klient'])
            if data.get('adres'):
                qs = qs.filter(adres__icontains=data['adres'])
            if data.get('wysylka_typ'):
                qs = qs.filter(wysylka_typ=data['wysylka_typ'])
            if data.get('sortuj'):
                qs = qs.order_by(*data.getlist('sortuj'))
        self.object_list = qs
        context = self.get_context_data()
        context['form'] = form
        return self.render_to_response(context)

class ZamowienieDetailView(LoginRequiredMixin, DetailView):
    model = Zamowienie

class ZamowienieCreateView(CreateView):
    model = Zamowienie
    fields = ['klient', 'adres', 'wysylka_typ', 'wysylka_adres', 'email', 'telefon']
    success_url = '/produkty/'

    def get_context_data(self, *args, **kwargs):
        if not 'form' in kwargs:
            kwargs['form'] = self.get_form(self.get_form_class())
        context = super().get_context_data(*args, **kwargs)
        try:
            context['nieprzeczytane'] = self.request.user.wiadomosc_set\
                    .filter(odczytana=False).count()
        except AttributeError:
            pass
        return context

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs(*args, **kwargs)
        kwargs['instance'] = Zamowienie()
        return kwargs

    def get_form(self, form_class, *args, **kwargs):
        if hasattr(self.request.user, 'pracownik'):
            self.fields.extend(['komentarz','opis'])
        else:
            self.fields.append('komentarz_klient')

        def _clean(self):
            d = self.cleaned_data
            if d['wysylka_typ'] == Zamowienie.WYSYLKA_TYP_PACZKOMAT and not d.get('wysylka_adres'):
                raise forms.ValidationError('Wybierając typ wysyłki "paczkomat" należy uzupełnić pole "wysyłka adres" adresem paczkomatu.')
            return d
        
        form_class.clean = _clean
        form = super().get_form(form_class, *args, **kwargs)
        if self.request.user.is_authenticated and self.request.user.klient:
            del form.fields['klient']
            form.instance.user = self.request.user
            form.fields['adres'].required = False
        else:
            form.fields['klient'].label = u'Imię i nazwisko'
        return form

    def form_valid(self, form):
        try:
            koszyk = self.request.session['koszyk']['produkt_map']
        except KeyError:
            if self.request.user.is_authenticated and hasattr(self.request.user, 'pracownik'):
                obj = form.save()
                messages.success(
                        self.request, 
                        ('Twoje zamówienie zostało przyjęte do realizacji! <br> '
                            'Twój nr zamówienia to: {} . Zapisz go pośpiesznie może '
                            'być potrzebny do śledzenia przeysłki.').format(obj.nr_zamowienia)
                        )
                return redirect(self.success_url)
            messages.error(self.request, 'Nie można wykonać akcji.')
            return redirect(self.success_url)
            
        form.save()
        zamowienie = form.instance
        produkt_map = {str(p.id): p for p in Produkt.objects.filter(pk__in=koszyk)}
        aktualny_brak_produktu = ''
        for k,v in koszyk.items():
            if not produkt_map[k].czy_dostepny(v):
                aktualny_brak_produktu += '{} - brakująca ilosc {} <br>'.format(produkt_map[k], produkt_map[k].magazyn_roznica_sprawdz(v))

            ZamowienieProdukt(
                zamowienie=zamowienie,
                produkt=produkt_map[k],
                cena=produkt_map[k].cena,
                ilosc=v
                ).save()
        if aktualny_brak_produktu:
            if zamowienie.komentarz:
                aktualny_brak_produktu += zamowienie.komentarz
            Zamowienie.objects.filter(pk=zamowienie.id).update(komentarz=aktaulny_brak_produktu)

        messages.success(
                self.request, 
                ('Twoje zamówienie zostało przyjęte do realizacji! <br> '
                    'Twój nr zamówienia to: {} . <br> Zapisz go pośpiesznie może '
                    'być potrzebny do śledzenia przeysłki.').format(zamowienie.nr_zamowienia)
                )
        del self.request.session['koszyk']
        ZamowienieStatus.objects.create(
                zamowienie=form.instance, 
                kto_id=self.request.user.id,
                status=ZamowienieStatus.STATUS_OCZEKUJE,
                )
        return redirect(self.request.GET.get('next') or self.success_url)

    def post(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form(self.get_form_class())
        if form.is_valid():
            return self.form_valid(form)
        return self.form_invalid(form)



class ZamowienieUpdateView(LoginRequiredMixin, UpdateView):
    model = Zamowienie
    fields = ['nr_zamowienia','klient','adres','wysylka_typ','wysylka_adres',
            'email','telefon','zrealizowane','opis','komentarz']
    success_url = '/zamowienia/'

    def form_valid(self, form):
        d = form.cleaned_data
        poprzedni = Zamowienie.objects.get(pk=form.instance.id)
        if not poprzedni.zrealizowane and d['zrealizowane']:
            form.instance.realizacja_kto = self.request.user
            form.instance.data_realizacji = datetime.datetime.now()
        elif poprzedni.zrealizowane and not d['zrealizowane']:
            form.instance.realizacja_kto, form.instance.data_realizacji = None, None
        form.save()
        return redirect(self.request.GET.get('next') or self.success_url)

class ZamowienieQuickUpdateView(LoginRequiredMixin, UpdateView):
    model = Zamowienie
    fields = ['opis','komentarz',]
    template_name = 'default_form.html'
    success_url = '/zamowienia/'

    def get(self, *args, **kwargs):
        self.object = self.get_object()
        if self.kwargs.get('zrealizowane_zmien'):
            self.object.zrealizowane = not self.object.zrealizowane
            self.object.data_realizacji = datetime.datetime.now()
            self.object.realizacja_kto = self.request.user
            self.object.save()
            return redirect(self.request.GET.get('next') or self.success_url)
        return super().get(*args, **kwargs)


class ZamowienieDeleteView(LoginRequiredMixin, DeleteView):
    model = Zamowienie
    success_url = '/zamowienia/'
    template_name = 'default_confirm_delete.html'

    def delete(self, *args, **kwargs):
        from django.db.models import ProtectedError
        try:
            return super().delete(*args, **kwargs)
        except ProtectedError:
            messages.error(self.request, 'Błąd. Zamowienie jest zrealizowane lub posiada powiązane produkty.')
            return redirect(self.success_url)


class ZamowienieProduktMixin(LoginRequiredMixin):
    model = ZamowienieProdukt
    fields = ['produkt','cena','ilosc','komentarz']
    template_name = 'default_form.html'
    
    def get_object(self, *args, **kwargs):
        obj = super().get_object(*args, **kwargs)
        self.success_url = '/zamowienie/{}'.format(obj.zamowienie.id)
        return obj

    def get_success_url(self, *args, **kwargs):
        self.success_url = self.request.GET.get('next')
        return super().get_success_url(*args, **kwargs)

class ZamowienieProduktCreateView(ZamowienieProduktMixin, CreateView): 
    def get_form_kwargs(self, **kwargs):
        kwargs = super().get_form_kwargs(**kwargs)
        kwargs['instance'] = ZamowienieProdukt()
        kwargs['instance'].zamowienie = Zamowienie(pk=self.kwargs['zamowienie_pk'])
        return kwargs

class ZamowienieProduktUpdateView(ZamowienieProduktMixin, UpdateView): pass
class ZamowienieProduktDeleteView(ZamowienieProduktMixin, DeleteView):
    template_name = 'default_confirm_delete.html'

    def delete(self, *args, **kwargs):
        self.object = self.get_object()
        if self.object.zamowienie.zrealizowane:
            messages.error(self.request, 'Nie można usunąć produktu ze zrealizowanego zamówienia.')
            return redirect(self.success_url)
        return super().delete(*args, **kwargs)


class ZamowienieStatusMixin(LoginRequiredMixin):
    model = ZamowienieStatus
    fields = ['status','komentarz']
    template_name = 'default_form.html'
    
    def get_object(self, *args, **kwargs):
        obj = super().get_object(*args, **kwargs)
        self.success_url = '/zamowienie/{}'.format(obj.zamowienie.id)
        return obj

    def get_success_url(self, *args, **kwargs):
        self.success_url = self.request.GET.get('next')
        return super().get_success_url(*args, **kwargs)

class ZamowienieStatusCreateView(ZamowienieStatusMixin, CreateView): 
    def get_form_kwargs(self, **kwargs):
        kwargs = super().get_form_kwargs(**kwargs)
        kwargs['instance'] = ZamowienieStatus()
        kwargs['instance'].zamowienie = Zamowienie(pk=self.kwargs['zamowienie_pk'])
        kwargs['instance'].kto = self.request.user
        return kwargs

class ZamowienieStatusUpdateView(ZamowienieStatusMixin, UpdateView): pass

class ZamowienieStatusDeleteView(ZamowienieStatusMixin, DeleteView):
    template_name = 'default_confirm_delete.html'


class MagazynFormFilter(forms.Form):
    produkt = forms.CharField(required=False)
    zamowione_od = forms.IntegerField(required=False)
    zamowione_do = forms.IntegerField(required=False)
    wolne_od = forms.IntegerField(required=False)
    wolne_do = forms.IntegerField(required=False)
    sortuj = forms.MultipleChoiceField(required=False, 
            choices=[
                ('produkt__nazwa','nazwa produktu A-Z'),
                ('-produkt__nazwa','nazwa produktu Z-A'),
                ('produkt__marka','marka produktu A-Z'),
                ('-produkt__marka','marka produktu Z-A'),
                ('wolny','wolny rosnąco'),
                ('-wolny','wolny malejąco'),
                ])

class MagazynListView(LoginRequiredMixin, ListView):
    model = Magazyn

    def get(self, *args, **kwargs):
        magazyn_pusty = Magazyn.objects.pusty_sprawdz() 
        if magazyn_pusty:
            messages.error(self.request, magazyn_pusty)
        qs = self.get_queryset()
        data = self.request.GET
        if not data:
            form = MagazynFormFilter()
        else:
            form = MagazynFormFilter(data)
            if data.get('produkt'):
                for i in data.get('produkt').split():
                    qs = qs.filter(
                        Q(produkt__nazwa__icontains=i)
                        |Q(produkt__marka__icontains=i)
                    )
            if data.get('wolne_od'):
                qs = qs.filter(wolny__gte=data['wolne_od'])
            if data.get('wolne_do'):
                qs = qs.filter(wolny__lte=data['wolne_do'])
            if data.get('zamowione_od'):
                qs = qs.filter(zamowione__gte=data['zamowione_od'])
            if data.get('zamowione_do'):
                qs = qs.filter(zamowione__lte=data['zamowione_do'])
            if data.get('sortuj'):
                qs = qs.order_by(*data.getlist('sortuj'))
        self.object_list = qs
        context = self.get_context_data()
        context['form'] = form
        for i in self.object_list:
            if i.wolny <= i.ilosc_min:
                i.poziom = 'red'
            elif i.wolny <= i.ilosc_max*0.30:
                i.poziom = 'yellow'
            elif i.wolny < i.ilosc_max:
                i.poziom = 'lime'
            else:
                i.poziom = 'mediumblue'
        return self.render_to_response(context)

class MagazynDetailView(LoginRequiredMixin, DetailView):
    model = Magazyn

class MagazynCreateView(LoginRequiredMixin, CreateView):
    model = Magazyn
    fields = ['produkt', 'ilosc_min', 'ilosc_max']
    success_url = '/magazyn/'
    template_name = 'default_form.html'


class MagazynUpdateView(LoginRequiredMixin, UpdateView):
    model = Magazyn
    fields = ['ilosc_min','ilosc_max']
    success_url = '/magazyn/'
    template_name = 'default_form.html'

class MagazynDeleteView(LoginRequiredMixin, DeleteView):
    model = Magazyn
    success_url = '/magazyn/'
    template_name = 'default_confirm_delete.html'


class MagazynPrzyjecieFormFilter(forms.Form):
    produkt = forms.CharField(required=False)
    ilosc_od = forms.IntegerField(required=False)
    ilosc_do = forms.IntegerField(required=False)
    kto = forms.ModelMultipleChoiceField(required=False, label='Przyjmujący', queryset=User.objects.filter(klient=False))
    kiedy_od = forms.DateTimeField(required=False)
    kiedy_do = forms.DateTimeField(required=False)
    sortuj = forms.MultipleChoiceField(required=False, 
            choices=[
                ('magazyn__produkt__nazwa','nazwa produktu A-Z'),
                ('-magazyn__produkt__nazwa','nazwa produktu Z-A'),
                ('magazyn__produkt__marka','marka produktu A-Z'),
                ('-magazyn__produkt__marka','marka produktu Z-A'),
                ('kiedy','wolny rosnąco'),
                ('-kiedy','wolny malejąco'),
                ])

class MagazynPrzyjecieListView(LoginRequiredMixin, ListView):
    model = MagazynPrzyjecie

    def get(self, *args, **kwargs):
        qs = self.get_queryset()
        data = self.request.GET
        if not data:
            form = MagazynPrzyjecieFormFilter()
        else:
            form = MagazynPrzyjecieFormFilter(data)
            if data.get('produkt'):
                for i in data.get('produkt').split():
                    qs = qs.filter(
                        Q(magazyn__produkt__nazwa__icontains=i)
                        |Q(magazyn__produkt__marka__icontains=i)
                    )
            if data.get('kto'):
                qs = qs.filter(kto__in=data['kto'])
            if data.get('ilosc_od'):
                qs = qs.filter(ilosc__gte=data['ilosc_od'])
            if data.get('ilosc_do'):
                qs = qs.filter(ilosc__lte=data['ilosc_do'])
            if data.get('kiedy_od'):
                qs = qs.filter(kiedy__gte=data['kiedy_od'])
            if data.get('kiedy_do'):
                qs = qs.filter(kiedy__lte=data['kiedy_do'])
            if data.get('sortuj'):
                qs = qs.order_by(*data.getlist('sortuj'))
        self.object_list = qs
        context = self.get_context_data()
        context['form'] = form
        return self.render_to_response(context)

class MagazynPrzyjecieCreateView(LoginRequiredMixin, CreateView):
    model = MagazynPrzyjecie
    fields = ['magazyn', 'ilosc', 'kto']
    success_url = '/magazyn/przyjecie/'
    template_name = 'default_form.html'

    def get_form_kwargs(self, **kwargs):
        kwargs = super().get_form_kwargs(**kwargs)
        kwargs['instance'] = MagazynPrzyjecie()
        kwargs['instance'].kto = self.request.user
        return kwargs


class MagazynPrzyjecieUpdateView(LoginRequiredMixin, UpdateView):
    model = MagazynPrzyjecie
    fields = ['ilosc', 'kto']
    success_url = '/magazyn/przyjecie/'
    template_name = 'default_form.html'

class MagazynPrzyjecieDeleteView(LoginRequiredMixin, DeleteView):
    model = MagazynPrzyjecie
    success_url = '/magazyn/przyjecie/'
    template_name = 'default_confirm_delete.html'

class MagazynWydanieListView(LoginRequiredMixin, ListView):
    model = MagazynWydanie

    def get(self, *args, **kwargs):
        qs = self.get_queryset()
        data = self.request.GET
        if not data:
            form = MagazynPrzyjecieFormFilter()
        else:
            form = MagazynPrzyjecieFormFilter(data)
            if data.get('produkt'):
                for i in data.get('produkt').split():
                    qs = qs.filter(
                        Q(magazyn__produkt__nazwa__icontains=i)
                        |Q(magazyn__produkt__marka__icontains=i)
                    )
            if data.get('kto'):
                qs = qs.filter(kto__in=data['kto'])
            if data.get('ilosc_od'):
                qs = qs.filter(ilosc__gte=data['ilosc_od'])
            if data.get('ilosc_do'):
                qs = qs.filter(ilosc__lte=data['ilosc_do'])
            if data.get('kiedy_od'):
                qs = qs.filter(kiedy__gte=data['kiedy_od'])
            if data.get('kiedy_do'):
                qs = qs.filter(kiedy__lte=data['kiedy_do'])
            if data.get('sortuj'):
                qs = qs.order_by(*data.getlist('sortuj'))
        self.object_list = qs
        context = self.get_context_data()
        context['form'] = form
        return self.render_to_response(context)
