from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings

import re
import opentracing
from opentracing import Format
from opentracing.ext import tags
from opentracing_instrumentation import traced_function

tracer = settings.OPENTRACING_TRACING

# Create your views here.


def server_index(request):
    return HttpResponse("Hello, world. You're at the server index.")


@traced_function
def server_simple_view(request):
    import re
    regex = re.compile('^HTTP_')
    headers = dict((regex.sub('', header), value) for (header, value)
         in request.META.items() if header.startswith('HTTP_'))

    if 'KPN_TRACE_ID' in headers:
        headers['kpn-trace-id'] = headers.pop('KPN_TRACE_ID')

    span_ctx = tracer.extract(Format.HTTP_HEADERS, headers)
    span_tags = {tags.SPAN_KIND: tags.SPAN_KIND_RPC_SERVER}

    with tracer.start_span('server_simple', child_of=span_ctx, tags=span_tags) as span:
        return HttpResponse("This is a simple traced request.")


# @tracing.trace()
def server_log(request):
    tracer.active_span.log_event("Hello, world!")
    return HttpResponse("Something was logged")


# @tracing.trace()
def server_child_span(request):
    child_span = tracer.start_active_span("child span")
    child_span.close()
    return HttpResponse("A child span was created")
