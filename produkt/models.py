import datetime

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Produkt(models.Model):
    nazwa = models.CharField(max_length=300)
    cena = models.DecimalField(max_digits=100000, decimal_places=2, default=0)
    opis = models.TextField(blank=True)
    marka = models.CharField(max_length=300)
    obraz = models.ImageField(upload_to='obrazy/', blank=True, null=True)

    def __str__(self):
        return u'{} - {} {} zł'.format(self.nazwa, self.marka, self.cena)

    class Meta:
        ordering = ['nazwa', 'marka']

    def magazyn_roznica_sprawdz(self, ilosc):
        try:
            return self.magazyn.wolny - ilosc
        except Magazyn.DoesNotExists:
            return -ilosc

    def czy_dostepny(self, ilosc):
        if not hasattr(self, 'magazyn'):
            return False
        return self.magazyn_roznica_sprawdz(ilosc) >= 0



class Zamowienie(models.Model):
    WYSYLKA_TYP_KURIER = 1
    WYSYLKA_TYP_EKONOMICZNY = 2
    WYSYLKA_TYP_PRIORYTET = 3
    WYSYLKA_TYP_ODBIOR = 4
    WYSYLKA_TYP_PACZKOMAT = 5

    WYSYLKA_CHOICES = [
        (WYSYLKA_TYP_KURIER, u'kurier'),
        (WYSYLKA_TYP_EKONOMICZNY, u'list ekonomiczny'),
        (WYSYLKA_TYP_PRIORYTET, u'list priorytetowy'),
        (WYSYLKA_TYP_PACZKOMAT, u'odbiór osobisty'),
        (WYSYLKA_TYP_PACZKOMAT, u'paczkomat'),
        ]

    nr_zamowienia = models.CharField(u'numer zamówienia', max_length=50)
    klient = models.CharField(max_length=300)
    user = models.ForeignKey(User, null=True, on_delete=models.PROTECT)
    adres = models.CharField(max_length=500)
    wysylka_typ = models.IntegerField(u'typ wysyłki', choices=WYSYLKA_CHOICES, default=WYSYLKA_TYP_EKONOMICZNY)
    wysylka_adres = models.CharField(u'adres wysyłki', max_length=500, blank=True,
            help_text='wypełnij jeśli adres wysyłki jest inny niż adres klienta')
    email = models.EmailField(blank=True)
    telefon = models.PositiveIntegerField(u'numer telefonu', null=True, blank=True)
    zrealizowane = models.BooleanField(u'czy zrealizowane', default=False)
    opis = models.TextField('Dodatkowe informacje', blank=True)
    komentarz = models.TextField('Komentarz pracownika', blank=True, help_text='nie widzialny dla klienta')
    komentarz_klient = models.TextField('Dodatkowe infomacje klienta', blank=True)
    data_zamowienia = models.DateTimeField(editable=False, auto_now_add=True)
    data_realizacji = models.DateTimeField(editable=False, null=True)
    realizacja_kto = models.ForeignKey(User, null=True, on_delete=models.PROTECT,
            related_name='zamowienie_realizacja_kto_set')

    class Meta:
        ordering = ['-data_zamowienia']

    def __str__(self):
        return 'Zamówienie nr {}'.format(self.nr_zamowienia)

    @property
    def get_wartosc(self):
        return sum(map(lambda x: x[0]*x[1] , self.zamowienieprodukt_set.values_list('cena','ilosc')))

    def numer_generuj(self):
        data = datetime.date.today().timetuple()[:3]
        nr = Zamowienie.objects.filter(data_zamowienia__year=data[0], data_zamowienia__month=data[1]).count() + 1
        return '{}/{}/{}/{}'.format(nr, *data[::-1])

    def czy_produkty_niedostepne(self):
        produkt_map = {}
        for z_produkt in ZamowienieProdukt.objects.filter(zamowienie=self):
            dostepne = z_produkt.produkt.magazyn.wolne - z_produkt.ilosc
            if dostepne < 0:
                produkt_map[z_produkt] = True
        return produkt_map

    def get_status(self):
        return self.zamowieniestatus_set.all().first()


    def save(self, *args, **kwargs):
        nowy = not self.id
        if nowy:
            self.nr_zamowienia = self.numer_generuj()
        if nowy and self.user:
            self.klient = '{}'.format(self.user)
            if not self.adres:
                self.adres = self.user.adres
            if not self.telefon:
                self.telefon = self.user.telefon
            if not self.email:
                self.email = self.user.email
        super().save(*args, **kwargs)
        if nowy:
            return

        if self.zrealizowane:
            for z_produkt in ZamowienieProdukt.objects.filter(zamowienie=self):
                MagazynWydanie.objects.create(
                    magazyn=z_produkt.produkt.magazyn,
                    ilosc=z_produkt.ilosc,
                    kto=self.realizacja_kto,
                    )
            return

        for z_produkt in ZamowienieProdukt.objects.filter(zamowienie=self):
            for i in MagazynWydanie.objects.filter(magazyn=z_produkt.produkt.magazyn):
                i.delete()

        

class ZamowienieProdukt(models.Model):
    produkt = models.ForeignKey(Produkt, on_delete=models.PROTECT)
    zamowienie = models.ForeignKey(Zamowienie, on_delete=models.PROTECT)
    cena = models.DecimalField(max_digits=100000, decimal_places=2, default=0)
    ilosc = models.PositiveIntegerField(u'ilość', default=0)
    komentarz = models.TextField(blank=True)

    class Meta:
        ordering = ['produkt__nazwa', 'produkt__marka']

    def __str__(self):
        return '{} - {} - {}'.format(self.zamowienie.nr_zamowienia, self.produkt.nazwa, self.produkt.marka)

    @property
    def get_wartosc(self):
        return round(self.cena*self.ilosc, 2)

    def save(self, *args, **kwargs):
        nowy = not self.id
        if not nowy:
            poprzedni = ZamowienieProdukt.objects.get(pk=self.id)
        super().save(*args, **kwargs)
        if nowy:
            self.produkt.magazyn.produkt_zamowienie_zmien(self.ilosc)
            return
        if poprzedni.ilosc != self.ilosc:
            roznica = poprzedni.ilosc - self.ilosc
            if self.produkt.magazyn.wolny < roznica:
                raise Exception('Stan magazynu nie pozwana na zmianę.')
            self.produkt.magazyn.produkt_zamowienie_zmien(-roznica)

    def delete(self, *args, **kwargs):
        magazyn = self.produkt.magazyn
        ilosc = self.ilosc
        zrealizowane = self.zamowienie.zrealizowane
        super().delete(*args, **kwargs)
        magazyn.produkt_zamowienie_zmien(-ilosc)

class ZamowienieStatus(models.Model):
    STATUS_OCZEKUJE = 1
    STATUS_REALIZACJA = 2
    STATUS_WYSLANE = 3
    STATUS_ANULOWANE = 4 
    STATUS_CHOICES = [
        (STATUS_OCZEKUJE, 'oczekuje'),
        (STATUS_REALIZACJA, 'w realizacji'),
        (STATUS_WYSLANE, 'wysłano'),
        (STATUS_ANULOWANE, 'anulowane'),
            ]

    zamowienie = models.ForeignKey(Zamowienie, on_delete=models.PROTECT)
    status = models.PositiveIntegerField(choices=STATUS_CHOICES)
    komentarz = models.TextField(blank=True)
    data = models.DateTimeField(editable=False, auto_now=True)
    kto = models.ForeignKey(User, editable=False, null=True, on_delete=models.PROTECT,
            related_name='zamowienie_status_kto_set')
    
    class Meta:
        ordering = ['zamowienie','-data']

    def __str__(self):
        return '{} - {}'.format(self.get_status_display(), self.zamowienie.nr_zamowienia)



class MagazynUtils(models.Manager):
    def pusty_sprawdz(cls):
        if Magazyn.objects.count() == 0 or not Magazyn.objects.filter(wolny__gt=0).exists():
            return u'UWAGA: Magazyn jest pusty!'

class Magazyn(models.Model):
    produkt = models.OneToOneField(Produkt, on_delete=models.PROTECT)
    ilosc = models.IntegerField('Ilość', editable=False, default=0)
    ilosc_min = models.IntegerField('Minimalna ilość', default=0)
    ilosc_max = models.IntegerField('Maksymalna ilość', default=0)
    wolny = models.IntegerField(editable=False, default=0)
    zamowiony = models.IntegerField(editable=False, default=0)
    sprzedany = models.IntegerField(editable=False, default=0)

    objects = MagazynUtils()

    def __str__(self):
        return '{}'.format(self.produkt)

    def produkt_dostep_sprawdz(self, ilosc):
        if self.ilosc - ilosc < 0:
            return 'Stan magazynu nie pozwala na zmianę.'

    def produkt_zamowienie_zmien(self, ilosc):
        self.wolny -= ilosc
        self.zamowiony += ilosc
        self.save()

    def produkt_przyjecie_zmien(self, ilosc):
        self.ilosc += ilosc
        self.wolny += ilosc
        self.save()

    def produkt_wydanie_zmien(self, ilosc):
        self.zamowiony -= ilosc
        self.sprzedany += ilosc
        self.save()
  

class MagazynPrzyjecie(models.Model):
    magazyn = models.ForeignKey(Magazyn, on_delete=models.PROTECT)
    ilosc = models.IntegerField('Ilość', default=0)
    kiedy = models.DateTimeField(auto_now_add=True)
    kto = models.ForeignKey(User, on_delete=models.PROTECT)

    def __str__(self):
        return '{}, {}'.format(self.magazyn.produkt, self.kiedy)

    def save(self, *args, **kwargs):
        nowy = not self.id
        super().save(*args, **kwargs)
        if nowy:
            self.magazyn.produkt_przyjecie_zmien(self.ilosc)

    def delete(self, *args, **kwargs):
        if self.magazyn.wolny - self.ilosc < 0:
            raise Exception(u'Stan magazynu nie pozwala na wybraną akcję.')
        magazyn = self.magazyn
        ilosc = self.ilosc
        super().delete(*args, **kwargs)
        self.magazyn.produkt_przyjecie_zmien(-self.ilosc)


class MagazynWydanie(models.Model):
    magazyn = models.ForeignKey(Magazyn, on_delete=models.PROTECT)
    ilosc = models.IntegerField('Ilość', editable=False, default=0)
    kiedy = models.DateTimeField(auto_now_add=True)
    kto = models.ForeignKey(User, on_delete=models.PROTECT)

    def save(self, *args, **kwargs):
        nowy = not self.id
        super().save(*args, **kwargs)
        if nowy:
            self.magazyn.produkt_wydanie_zmien(self.ilosc)

    def delete(self, *args, **kwargs):
        magazyn = self.magazyn
        ilosc = self.ilosc
        super().delete(*args, **kwargs)
        magazyn.produkt_wydanie_zmien(-ilosc)
