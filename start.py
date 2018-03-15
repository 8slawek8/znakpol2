import django, os                                                                  
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sklep.settings")                    
django.setup()   

from django.db import transaction
from django.contrib.auth.models import Group as Stanowisko

from pracownik.models import Uzytkownik, Pracownik
from wiadomosc.models import Wiadomosc
from produkt.models import Produkt, Magazyn, MagazynPrzyjecie


def setup():
    u1 = Uzytkownik.objects.create(
            username='pawel', 
            first_name='Paweł', 
            last_name='Bars',
            is_superuser=True,
            adres='Koniczynki 4, 78-349 Bytom',
            telefon=99988800,
            )
    u2 =Uzytkownik.objects.create(
            username='beata', 
            first_name='Beata', 
            last_name='Patulska',
            adres='Dębowiec 34, 78-349 Bytom',
            telefon=99988899,
            )
    u3 = Uzytkownik.objects.create(
            username='mariusz', 
            first_name='Mariusz', 
            last_name='Nowakowski',
            adres='Borkowo 34, 78-893 Bydgoszcz',
            telefon=99988877,
            )
    u4 = Uzytkownik.objects.create(
            username='adam', 
            first_name='Adam', 
            last_name='Bornaś',
            is_superuser=True,
            adres='Klekotki 23, 78-349 Bytom',
            telefon=78998790,
            )
    u5 = Uzytkownik.objects.create(
            username='dariusz', 
            first_name='Dariusz', 
            last_name='Pałęcki',
            adres='Zegarki 3/4, 78-341 Kędziorno',
            telefon=78998794,
            )
    u6 = Uzytkownik.objects.create(
            username='joanna', 
            first_name='Joanna', 
            last_name='Pałakowska',
            adres='Klekotki 33, 78-341 Kędziorno',
            telefon=78998793,
            email='joanna@joanna.pl'
            )
    u7 = Uzytkownik.objects.create(
            username='kazik', 
            first_name='Kazik', 
            last_name='Borowski',
            adres='Jabłonna 34, 73-441 Kowalewo',
            telefon=78333333,
            email='kazik@kazimierz.pl',
            klient=True,
            )
    for u in [u1,u2,u3,u4,u5,u6,u7]:
        u.set_password(u.username)
        u.save()
    for user, stanowisko_nazwa in [
            (u1, 'Manager'),
            (u2, 'Kierownik działu projektów'),
            (u3, 'Specjalista ds. produkcji i promocji'), 
            (u4, 'Administrator'),
            (u5, 'Magazynier'),
            (u6, 'Magazynier'),
            ]:
        stanowisko, _ = Stanowisko.objects.get_or_create(name=stanowisko_nazwa)
        Pracownik.objects.create(user=user, stanowisko=stanowisko)

    w1 = Wiadomosc.objects.create(
            temat='Zapytanie ofertowe',
            tresc=('Witam, \n czy istnieje możliwość zamówienia znaków B4 w ilości '
            '10 000 na drogę krajową nr S8? \n wszelkie szczegóły jeśli są państwo zainteresowani '
            'wyjaśnie po kontakcie telefonicznym: 89789797. \n Pozdrawiam Grzegorz'),
            nadawca=None,
            )
    w1.odbiorca_list.add(u2)

    w2 = Wiadomosc.objects.create(
            temat='Zapytanie ofertowe',
            tresc=('Witam, \n czy produkują państwo tablice nad autostradami? '
            'Jaki jest koszt projektu i wykonania? '
            'Proszę o pilny kontakt: 897328394 - Bożenka'),
            nadawca=None,
            odczytana=True,
            )
    w2.odbiorca_list.add(u2)

    w3 = Wiadomosc.objects.create(
            temat='Witamy w systemie',
            tresc=('Gorąco witamy w systemie ZnakPoL, życzmy udanych zakupów i miłej pracy'),
            nadawca=u4,
            )
    w3.odbiorca_list.add(u1,u2,u3,u4,u5,u6,u7)

    w4 = Wiadomosc.objects.create(
            temat='Zapytanie ofertowe',
            tresc=('Witam, \n piszę ponownie w sprawnie zapytania czy produkują państwo tablice nad autostradami? '
            'Jaki jest koszt projektu i wykonania? '
            'Proszę o pilny kontakt: 897328394 - Bożenka email: bozenka@bozenka.pl Temat bardzo pilny'),
            nadawca=None,
            )
    w4.odbiorca_list.add(u2)

    w5 = Wiadomosc.objects.create(
            temat='Projekt tablicy dwustronne',
            tresc=('Pani Beatko poproszę o przygotowanie projektu tablicy dwustronnej. '
            ' \n Pozdrawiam serdecznie Paweł'),
            nadawca=u1,
            )
    w5.odbiorca_list.add(u2)

    lista_magazyn = []
    for nazwa, cena, opis, marka in [
            ('Usluga transportowa - Bus do 3,5 tony', 5, 'Cena podana za 1 km', 'ZnakPoL'),
            ('Usluga transportowa - Bus powyżej 3,5 tony', 10, 'Cena podana za 1 km', 'ZnakPoL'),
            ('Usluga transportowa - TIR transport zagraniczny', 20, 'Cena podana za 1 km', 'ZnakPoL'),
            ('Usluga transportowa - TIR transport zagraniczny', 40, 'Cena podana za 1 km', 'ZnakPoL'),
            ('Projekt wykonania barier drogowych', 500, 'Cena orientacyjna - wycena indywidualna', 'ZnakPoL'),
            ('Projekt wykonania słupków drogowych', 200, 'Cena orientacyjna - wycena indywidualna', 'ZnakPoL'),
            ('Projekt wykonania stojaki na rowery', 400, 'Cena orientacyjna - wycena indywidualna', 'ZnakPoL'),
            ('Projekt wykonania stojaki kręte na rowery', 650, 'Cena orientacyjna - wycena indywidualna', 'ZnakPoL'),
            ('A-1', 120, '', 'ZnakPoL'),
            ('A-11', 120, '', 'ZnakPoL'),
            ('A-10', 150, '', 'ZnakPoL'),
            ('A-5', 100, '', 'ZnakPoL'),
            ('D-10', 120, '', 'ZnakPoL'),
            ('A-11', 120, 'Znak z folią antyroszeniową', 'ZnakPoL'),
            ('D-11', 150, '', 'EroZnak'),
            ('A-5', 100, 'Projekt', 'EroZnak'),
            ('B-1', 120, '', 'ZnakPoL'),
            ('B-2', 130, '', 'ZnakPoL'),
            ('B-15', 130, '', 'ZnakPoL'),
            ('B-20', 110, 'Znak z folią antyroszeniową', 'ZnakPoL'),
            ('B-23', 150, '', 'EroZnak'),
            ('C-1', 100, '', 'EroZnak'),
            ('C-10', 130, '', 'ZnakPoL'),
            ('C-11', 130, '', 'ZnakPoL'),
            ('C-12', 110, 'Znak z folią antyroszeniową', 'ZnakPoL'),
            ('C-13', 150, '', 'EroZnak'),
            ('D-16', 100, '', 'EroZnak'),
            ('T-14', 90, 'Znak z folią antyroszeniową', 'ZnakPoL'),
            ('T-16', 80, '', 'ZnakPoL'),
            ('T-29', 100, '', 'ZnakPoL'),
            ('T-30e', 80, 'Projekt', 'EroZnak'),
            ('T-30f', 90, 'Projekt', 'EroZnak'),
            ('Usługa montażowa znaków', 50, 'Za sztukę, wielkość znaku do 1 metrów', 'ZnakPoL'),
            ('Usługa montażowa tablic', 280, 'Za sztukę nie przekraczającą 4 mertów', 'ZnakPoL'),
            ]:
        p = Produkt.objects.create(nazwa=nazwa, cena=cena, opis=opis, marka=marka)
        lista_magazyn.append(Magazyn.objects.create(produkt=p, ilosc_min=10, ilosc_max=400))
    for m in lista_magazyn[::3]:
        MagazynPrzyjecie.objects.create(magazyn=m, ilosc=300, kto=u6)
    for m in lista_magazyn[::4]:
        MagazynPrzyjecie.objects.create(magazyn=m, ilosc=80, kto=u5)
    for m in lista_magazyn[::5]:
        MagazynPrzyjecie.objects.create(magazyn=m, ilosc=4, kto=u5)
    for m in lista_magazyn[::10]:
        MagazynPrzyjecie.objects.create(magazyn=m, ilosc=500, kto=u6)


with transaction.atomic():
    setup()
