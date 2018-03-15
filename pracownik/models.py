from django.db import models

from django.contrib.auth.models import AbstractUser, Group as Stanowisko


class Uzytkownik(AbstractUser):
    adres = models.CharField(max_length=500)
    telefon = models.PositiveIntegerField(u'numer telefonu', blank=True, null=True)
    klient = models.BooleanField(default=False)
    zdjecie = models.ImageField('Zdjęcie', upload_to='obrazy/', blank=True, null=True)

    def get_nazwa(self):
        if self.first_name or self.last_name:
            return '{} {}'.format(self.first_name, self.last_name)
        if self.email:
            return self.email
        return self.username

    def __str__(self):
        try:
            stanowisko = ' - ' + self.pracownik.stanowisko.nazwa
        except AttributeError:
            stanowisko = ''
        return '{}{}'.format(self.get_nazwa(), stanowisko)


class Pracownik(models.Model):
    user = models.OneToOneField(Uzytkownik, on_delete=models.PROTECT, related_name='pracownik')
    stanowisko = models.ForeignKey(Stanowisko, on_delete=models.PROTECT)

    def __str__(self):
        return '{} - {}'.format(self.stanowisko, self.user)
