"""
WSGI config for jaeger_tracing_intro project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
from opentracing_instrumentation.client_hooks import install_all_patches
from opentracing_instrumentation.http_server import WSGIRequestWrapper, before_request
from opentracing_instrumentation.request_context import RequestContextManager

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jaeger_tracing_intro.settings')

application = get_wsgi_application()


from uwsgidecorators import postfork

@postfork
def reconnect_to_db():
    import jaeger_client
    conf = jaeger_client.Config(config={
        'sampler': {'type': 'const', 'param': 1},
        'trace_id_header': 'kpn_trace_id',
    }, service_name='django-jaeger', validate=True)

    conf.initialize_tracer()
    install_all_patches()


def create_wsgi_middleware(other_wsgi, tracer=None):
    """
    Create a wrapper middleware for another WSGI response handler.
    If tracer is not passed in, 'opentracing.tracer' is used.
    """

    def wsgi_tracing_middleware(environ, start_response):
        # TODO find out if the route can be retrieved from somewhere

        request = WSGIRequestWrapper.from_wsgi_environ(environ)

        span = before_request(request=request, tracer=tracer)

        # Wrapper around the real start_response object to log
        # additional information to opentracing Span
        def start_response_wrapper(status, response_headers, exc_info=None):
            if exc_info is not None:
                span.set_tag('error', str(exc_info))
            span.finish()

            return start_response(status, response_headers)

        with RequestContextManager(span=span):
            return other_wsgi(environ, start_response_wrapper)

    return wsgi_tracing_middleware

application = create_wsgi_middleware(application)