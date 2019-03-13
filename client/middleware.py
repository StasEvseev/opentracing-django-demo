import opentracing
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from jaeger_client.reporter import NullReporter
from opentracing.ext import tags

from opentracing_instrumentation.request_context import RequestContextManager

tracer = settings.TRACER


def get_headers(request):
    headers = {}
    for k, v in request.META.items():
        k = k.lower().replace('_', '-')
        if k.startswith('http-'):
            k = k[5:]
        headers[k] = v

    return headers


class OpenTracingMiddleware(MiddlewareMixin):
    span = None
    orig_reporter = None

    def process_view(self, request, view_func, view_args, view_kwargs):
        # determine whether this middleware should be applied
        # NOTE: if tracing is on but not tracing all requests, then the tracing
        # occurs through decorator functions rather than middleware
        print('OpenTracingMiddleware:process_view', getattr(settings, 'TEST_SETTING'))

        headers = get_headers(request)

        try:
            span_ctx = tracer.tracer.extract(opentracing.Format.HTTP_HEADERS, headers)
        except (opentracing.InvalidCarrierException,
                opentracing.SpanContextCorruptedException):
            span_ctx = None

        if not span_ctx and getattr(settings, 'TEST_SETTING', None) == 'skip':
            #print(tracer.tracer.reporter)

            tracer.tracer.reporter.close()
            tracer.tracer.reporter = NullReporter()

        self._apply_tracing(request, view_func, tracer.tracer, span_ctx)
        self.request_context.__enter__()

    def _apply_tracing(self, request, view_func, tracer, span_ctx):
        """
        Helper function to avoid rewriting for middleware and decorator.
        Returns a new span from the request with logged attributes and
        correct operation name from the view_func.
        """
        # strip headers for trace info

        headers = get_headers(request)

        # start new span from trace info
        operation_name = view_func.__name__
        span = tracer.start_span(operation_name, child_of=span_ctx)

        # standard tags
        span.set_tag(tags.COMPONENT, 'django')
        span.set_tag(tags.SPAN_KIND, tags.SPAN_KIND_RPC_SERVER)
        span.set_tag(tags.HTTP_METHOD, request.method)
        span.set_tag(tags.HTTP_URL, request.get_full_path())

        self.request_context = RequestContextManager(span=span)
        self.span = span

    def _finish_tracing(self, request, response=None, error=None):
        if self.span is None:
            return

        if error is not None:
            self.span.set_tag(tags.ERROR, True)
            self.span.log_kv({
                'event': tags.ERROR,
                'error.object': error,
            })

        if response is not None:
            self.span.set_tag(tags.HTTP_STATUS_CODE, response.status_code)

        self.span.finish()
        self.request_context.__exit__()

    def process_exception(self, request, exception):
        print('PROCESS_EXCEPTION', str(exception))
        self.span.set_tag('error', str(exception))
        self._finish_tracing(request, error=exception)

    def process_response(self, request, response):
        print('PROCESS_RESPONSE', response)
        self._finish_tracing(request, response=response)
        return response
