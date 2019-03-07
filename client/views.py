from django.conf import settings
from django.http import HttpResponse
import requests
import aiohttp
import asyncio

import opentracing
import six
from opentracing.ext import tags
from opentracing import Format
import redis
from django.contrib.auth.models import User

from django.db.transaction import atomic
from opentracing_instrumentation import traced_function
from opentracing_instrumentation.request_context import get_current_span


tracer = settings.OPENTRACING_TRACING
# redis_opentracing.init_tracing(tracer)

client = redis.StrictRedis(host='host.docker.internal')

# jaeger_tracer = settings.OPENTRACING_JAEGER_CLIENT


# @tracing.trace()
def client_index(request):
    with tracer.start_span('test') as span:
        span.log_event('test_event')
    return HttpResponse("Client index page")


async def call_server(event_loop, url, headers, span):
    async with aiohttp.ClientSession(loop=event_loop, headers=headers) as aiohttp_client:
        try:
            response = await aiohttp_client.get(url)
            body = await response.text()
            print(response.status)
            return HttpResponse("Made a simple request")
        except aiohttp.ServerDisconnectedError as e:
            span.set_tag(tags.ERROR, True)
            return HttpResponse("Error: " + str(e))


@traced_function
# @tracer.trace()
def client_simple_view(request):
    event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(event_loop)

    url = "http://localhost:8000/server/simple"

    with tracer.start_span('client_simple', tags={
        tags.HTTP_METHOD: 'GET',
        tags.HTTP_URL: url,
        tags.PEER_SERVICE: 'KPN_PAYMENT',
        tags.SPAN_KIND: tags.SPAN_KIND_RPC_CLIENT,
    }, child_of=get_current_span()) as span:
        client.set('last_access', 'testvalue')

        with atomic():
            c = User.objects.count()
            print(c)

        headers = {}
        tracer.inject(span, Format.HTTP_HEADERS, headers)

        # resultst = event_loop.run_until_complete(asyncio.gather(
        #     asyncio.ensure_future(call_server(event_loop, url, headers, scope.span))
        # ))
        #
        # return resultst[0]

        try:
            response = requests.get(url, headers=headers)
            return HttpResponse("Made a simple request")
        except six.moves.urllib.error.URLError as e:
            span.set_tag(tags.ERROR, True)
            return HttpResponse("Error: " + str(e))


def server_call_service():

    pass


# @tracing.trace()
def client_log(request):
    url = "http://localhost:8000/server/log"
    new_request = six.moves.urllib.request.Request(url)
    inject_as_headers(tracer, tracer.active_span, new_request)
    try:
        response = requests.get(url)
        # response = six.moves.urllib.request.urlopen(new_request)
        return HttpResponse("Sent a request to log")
    except six.moves.urllib.error.URLError as e:
        return HttpResponse("Error: " + str(e))


# @tracing.trace()
def client_child_span(request):
    url = "http://localhost:8000/server/childspan"
    new_request = six.moves.urllib.request.Request(url)
    inject_as_headers(tracer, tracer.active_span, new_request)
    try:
        response = requests.get(url)
        # response = six.moves.urllib.request.urlopen(new_request)
        return HttpResponse("Sent a request that should produce an additional child span")
    except six.moves.urllib.error.URLError as e:
        return HttpResponse("Error: " + str(e))


def inject_as_headers(tracer, span, request):
    text_carrier = {}
    tracer.inject(span.context, opentracing.Format.TEXT_MAP, text_carrier)
    for k, v in six.iteritems(text_carrier):
        request.add_header(k,v)
