from django.contrib.auth.views import LoginView as DjangoLoginView
from django.views.generic import TemplateView

class HomeView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        try:
            context['nieprzeczytane'] = self.request.user.wiadomosc_set\
                    .filter(odczytana=False).count()
        except AttributeError:
            pass
        return context

class LoginView(DjangoLoginView):
    template_name = "login.html"

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        form.fields['username'].label = 'Login'
        return form
