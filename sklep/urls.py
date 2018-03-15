from django.contrib import admin
from django.urls import path
from django.conf.urls import url
from django.contrib.auth.views import LogoutView
from django.conf.urls.static import static
from django.conf import settings

from produkt import views as pv
from wiadomosc import views as wv
from pracownik import views as uv
from sklep import views as sv



urlpatterns = [
    path('admin/', admin.site.urls),
    url(r'^login/$', sv.LoginView.as_view(), name="login"),
    url(r'^logout/$', LogoutView.as_view(), name="logout"),
    url(r'^rejestracja/$', uv.RejestracjaView.as_view(), name='rejestracja'),
    url(r'^$', sv.HomeView.as_view(), name="home"),
    url(r'^produkty/$', pv.ProduktListView.as_view(), name='produkt-lista'),
    url(r'^produkt/(?P<pk>\d+)/$', pv.ProduktDetailView.as_view(), name='produkt-szczegoly'),
    url(r'^produkt/dodaj/$', pv.ProduktCreateView.as_view(), name='produkt-dodaj'),
    url(r'^produkt/(?P<pk>\d+)/edytuj/$', pv.ProduktUpdateView.as_view(), name='produkt-edytuj'),
    url(r'^produkt/(?P<pk>\d+)/usun/$', pv.ProduktDeleteView.as_view(), name='produkt-usun'),

    url(r'^koszyk/$', pv.KoszykListView.as_view(), name='koszyk-lista'),
    url(r'^koszyk/(?P<pk>\d+)/dodaj/$', pv.KoszykView.as_view(), {'koszyk-dodaj': True}, name='koszyk-dodaj'),
    url(r'^koszyk/(?P<pk>\d+)/usun/$', pv.KoszykView.as_view(), {'koszyk-usun': True}, name='koszyk-usun'),
    url(r'^koszyk/usun/calosc/$', pv.KoszykView.as_view(), {'koszyk-usun-calosc': True}, name='koszyk-usun-calosc'),

    url(r'^zamowienia/$', pv.ZamowienieListView.as_view(), name='zamowienie-lista'),
    url(r'^zamowienie/(?P<pk>\d+)/$', pv.ZamowienieDetailView.as_view(), name='zamowienie-szczegoly'),
    url(r'^zamowienie/dodaj/$', pv.ZamowienieCreateView.as_view(), name='zamowienie-dodaj'),
    url(r'^zamowienie/(?P<pk>\d+)/edytuj/$', pv.ZamowienieUpdateView.as_view(), name='zamowienie-edytuj'),
    url(r'^zamowienie/(?P<pk>\d+)/quick/edytuj/$', pv.ZamowienieQuickUpdateView.as_view(), name='zamowienie-quick-edytuj'),
    url(r'^zamowienie/(?P<pk>\d+)/zrealizowane/$', pv.ZamowienieQuickUpdateView.as_view(),
        {'zrealizowane_zmien': True}, name='zamowienie-zrealizowane'),
    url(r'^zamowienie/(?P<pk>\d+)/usun/$', pv.ZamowienieDeleteView.as_view(), name='zamowienie-usun'),

    url(r'^zamowienie/(?P<zamowienie_pk>\d+)/produkt/dodaj/$', pv.ZamowienieProduktCreateView.as_view(), name='zamowienie-produkt-dodaj'),
    url(r'^zamowienie/produkt/(?P<pk>\d+)/edytuj/$', pv.ZamowienieProduktUpdateView.as_view(), name='zamowienie-produkt-edytuj'),
    url(r'^zamowienie/produkt/(?P<pk>\d+)/usun/$', pv.ZamowienieProduktDeleteView.as_view(), name='zamowienie-produkt-usun'),

    url(r'^zamowienie/(?P<zamowienie_pk>\d+)/status/dodaj/$', pv.ZamowienieStatusCreateView.as_view(), name='zamowienie-status-dodaj'),
    url(r'^zamowienie/status/(?P<pk>\d+)/edytuj/$', pv.ZamowienieStatusUpdateView.as_view(), name='zamowienie-status-edytuj'),
    url(r'^zamowienie/status/(?P<pk>\d+)/usun/$', pv.ZamowienieStatusDeleteView.as_view(), name='zamowienie-status-usun'),

    url(r'^magazyn/$', pv.MagazynListView.as_view(), name='magazyn-lista'),
    url(r'^magazyn/(?P<pk>\d+)/$', pv.MagazynDetailView.as_view(), name='magazyn-szczegoly'),
    url(r'^magazyn/dodaj/$', pv.MagazynCreateView.as_view(), name='magazyn-dodaj'),
    url(r'^magazyn/(?P<pk>\d+)/edytuj/$', pv.MagazynUpdateView.as_view(), name='magazyn-edytuj'),
    url(r'^magazyn/(?P<pk>\d+)/usun/$', pv.MagazynDeleteView.as_view(), name='magazyn-usun'),

    url(r'^magazyn/przyjecie/$', pv.MagazynPrzyjecieListView.as_view(), name='magazyn-przyjecie-lista'),
    url(r'^magazyn/przyjecie/dodaj/$', pv.MagazynPrzyjecieCreateView.as_view(), name='magazyn-przyjecie-dodaj'),
    url(r'^magazyn/przyjecie/(?P<pk>\d+)/edytuj/$', pv.MagazynPrzyjecieUpdateView.as_view(), name='magazyn-przyjecie-edytuj'),
    url(r'^magazyn/przyjecie/(?P<pk>\d+)/usun/$', pv.MagazynPrzyjecieDeleteView.as_view(), name='magazyn-przyjecie-usun'),

    url(r'^magazyn/wydanie/$', pv.MagazynWydanieListView.as_view(), name='magazyn-wydanie-lista'),



    url(r'^wiadomosci/$', wv.WiadomoscListView.as_view(), name='wiadomosc-lista'),
    url(r'^wiadomosc/(?P<pk>\d+)/$', wv.WiadomoscDetailView.as_view(), name='wiadomosc-szczegoly'),
    url(r'^wiadomosc/dodaj/$', wv.WiadomoscCreateView.as_view(), name='wiadomosc-dodaj'),
    url(r'^wiadomosc/kontakt/dodaj/$', wv.WiadomoscKontaktCreateView.as_view(), name='wiadomosc-kontakt-dodaj'),
    url(r'^wiadomosc/promocja/dodaj/$', wv.WiadomoscPromocjaCreateView.as_view(), name='wiadomosc-promocja-dodaj'),
    url(r'^wiadomosc/(?P<pk>\d+)/odpowiedz/$', wv.WiadomoscOdpowiedzView.as_view(), name='wiadomosc-odpowiedz'),
    url(r'^wiadomosc/(?P<pk>\d+)/usun/$', wv.WiadomoscDeleteView.as_view(), name='wiadomosc-usun'),



    url(r'^uzytkownicy/$', uv.UzytkownikListView.as_view(), name='uzytkownik-lista'),
    url(r'^uzytkownik/(?P<pk>\d+)/$', uv.UzytkownikDetailView.as_view(), name='uzytkownik-szczegoly'),
    url(r'^uzytkownik/dodaj/$', uv.UzytkownikCreateView.as_view(), name='uzytkownik-dodaj'),
    url(r'^uzytkownik/(?P<pk>\d+)/edytuj/$', uv.UzytkownikUpdateView.as_view(), name='uzytkownik-edytuj'),
    url(r'^haslo/(?P<pk>\d+)/zmien/$', uv.ZmienHasloView.as_view(), name='zmien-haslo'),
    url(r'^uzytkownik/(?P<pk>\d+)/usun/$', uv.UzytkownikDeleteView.as_view(), name='uzytkownik-usun'),

    url(r'^stanowiska/$', uv.StanowiskoListView.as_view(), name='stanowisko-lista'),
    url(r'^stanowisko/(?P<pk>\d+)/$', uv.StanowiskoDetailView.as_view(), name='stanowisko-szczegoly'),
    url(r'^stanowisko/dodaj/$', uv.StanowiskoCreateView.as_view(), name='stanowisko-dodaj'),
    url(r'^stanowisko/(?P<pk>\d+)/edytuj/$', uv.StanowiskoUpdateView.as_view(), name='stanowisko-edytuj'),
    url(r'^stanowisko/(?P<pk>\d+)/usun/$', uv.StanowiskoDeleteView.as_view(), name='stanowisko-usun'),

    url(r'^pracownik/dodaj/$', uv.PracownikCreateView.as_view(), name='pracownik-dodaj'),
    url(r'^pracownik/(?P<pk>\d+)/edytuj/$', uv.PracownikUpdateView.as_view(), name='pracownik-edytuj'),
    url(r'^pracownik/(?P<pk>\d+)/usun/$', uv.PracownikDeleteView.as_view(), name='pracownik-usun'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
