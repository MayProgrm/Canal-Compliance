from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

class SecurityHeadersMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        if getattr(settings, 'DEBUG', False):
            csp = "default-src 'self' data: blob:; img-src 'self' data: blob:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; font-src 'self' data:; connect-src 'self' data: blob:; frame-ancestors 'none'; base-uri 'self'; form-action 'self'; object-src 'none'"
        else:
            csp = "default-src 'self'; img-src 'self' data: blob:; style-src 'self' 'unsafe-inline'; script-src 'self'; font-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'; object-src 'none'"
        response.headers.setdefault('Content-Security-Policy', csp)
        response.headers.setdefault('Referrer-Policy', 'no-referrer')
        response.headers.setdefault('Permissions-Policy', 'camera=(), microphone=(), geolocation=()')
        response.headers.setdefault('Cross-Origin-Opener-Policy', 'same-origin')
        response.headers.setdefault('Cross-Origin-Resource-Policy', 'same-origin')
        return response

class DevDisableCSRFMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if getattr(settings, 'DEBUG', False):
            setattr(request, '_dont_enforce_csrf_checks', True)
        return None
