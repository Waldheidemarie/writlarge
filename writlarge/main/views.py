from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import logout as auth_logout_view
from django.views.generic.base import TemplateView, View
from djangowind.views import logout as wind_logout_view

from writlarge.main.mixins import JSONResponseMixin


# returns important setting information for all web pages.
def django_settings(request):
    return {'settings':
            {'GOOGLE_MAP_API': getattr(settings, 'GOOGLE_MAP_API', '')}}


class IndexView(TemplateView):
    template_name = "main/index.html"


class LoginView(JSONResponseMixin, View):

    def post(self, request):
        request.session.set_test_cookie()
        login_form = AuthenticationForm(request, request.POST)
        if login_form.is_valid():
            login(request, login_form.get_user())
            if request.user is not None:
                next_url = request.POST.get('next', '/')
                return self.render_to_json_response({'next': next_url})

        return self.render_to_json_response({'error': True})


class LogoutView(LoginRequiredMixin, View):

    def get(self, request):
        if hasattr(settings, 'CAS_BASE'):
            return wind_logout_view(request, next_page="/")
        else:
            return auth_logout_view(request, "/")
