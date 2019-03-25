"""
WSGI config for jaeger_tracing_intro project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
from django.conf import settings


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jaeger_tracing_intro.settings')

application = get_wsgi_application()

from uwsgidecorators import postfork


@postfork
def reconnect_to_jaeger():
    """
    Do force reconnect to jaeger collector
    """
    import jaeger_client
    from opentracing_instrumentation.client_hooks import install_all_patches

    jaeger_client.Config._initialized = False
    settings.JAEGER_CONFIG.initialize_tracer()
    install_all_patches()
