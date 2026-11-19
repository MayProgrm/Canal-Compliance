import secrets

from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from urllib.parse import urlsplit


def csp_nonce(request):
    return {'csp_nonce': getattr(request, 'csp_nonce', '')}


class SecurityHeadersMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.csp_nonce = secrets.token_urlsafe(16)

    def process_response(self, request, response):
        nonce = getattr(request, 'csp_nonce', '')
        if getattr(settings, 'DEBUG', False):
            csp = "default-src 'self' data: blob:; img-src 'self' data: blob:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; font-src 'self' data:; connect-src 'self' data: blob:; frame-ancestors 'none'; base-uri 'self'; form-action 'self'; object-src 'none'"
        else:
            csp = f"default-src 'self'; img-src 'self' data: blob:; style-src 'self' 'unsafe-inline'; script-src 'self' 'nonce-{nonce}'; font-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'; object-src 'none'"
        response.headers.setdefault('Content-Security-Policy', csp)
        response.headers.setdefault('Referrer-Policy', 'no-referrer')
        response.headers.setdefault('Permissions-Policy', 'camera=(), microphone=(), geolocation=()')
        response.headers.setdefault('Cross-Origin-Opener-Policy', 'same-origin')
        response.headers.setdefault('Cross-Origin-Resource-Policy', 'same-origin')
        return response


class LocalCsrfOriginMiddleware(MiddlewareMixin):

    def process_view(self, request, callback, callback_args, callback_kwargs):
        if not settings.DEBUG or request.method != 'POST':
            return None
        origin = request.META.get('HTTP_ORIGIN')
        if not origin:
            return None
        has_csrf_cookie = bool(request.COOKIES.get(settings.CSRF_COOKIE_NAME))
        has_csrf_form_token = 'csrfmiddlewaretoken' in request.POST
        if not (has_csrf_cookie and has_csrf_form_token):
            return None
        try:
            host = request.get_host()
        except Exception:
            return None
        same_host = urlsplit(origin).netloc == host
        if same_host or origin == 'null':
            request.META.pop('HTTP_ORIGIN', None)
        return None
