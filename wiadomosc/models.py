from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Wiadomosc(models.Model):
    temat = models.CharField(blank=True, max_length=300)
    tresc = models.TextField('Treść', blank=True)
    nadawca = models.ForeignKey(User, related_name='nadawcawiadomosc_set', null=True, on_delete=models.PROTECT)
    odbiorca_list = models.ManyToManyField(User, verbose_name='Odbiorca')
    odczytana = models.BooleanField(default=False)
    data_nadania = models.DateTimeField(editable=False, auto_now_add=True)
    zalacznik = models.FileField(upload_to='pliki/', verbose_name='Załącznik', blank=True, null=True)

    class Meta:
        ordering = ['odczytana', '-data_nadania']
