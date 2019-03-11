from django.http import HttpResponse, StreamingHttpResponse
import requests
import aiohttp

import six
from opentracing.ext import tags
from opentracing import Format
import redis
from django.contrib.auth.models import User

from django.db.transaction import atomic
from opentracing_instrumentation.request_context import get_current_span

from opentracing import tracer

client = redis.StrictRedis(host='host.docker.internal')


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


def client_simple_view(request):
    url = "http://uwsgi:8080/fixed/v1/order/"

    client.set('last_access', 'testvalue')

    with atomic():
        c = User.objects.count()
        print(c)

    with tracer.start_span('client_simple', tags={
        tags.HTTP_METHOD: 'GET',
        tags.HTTP_URL: url,
        # tags.PEER_SERVICE: 'KPN_PAYMENT',
        tags.SPAN_KIND: tags.SPAN_KIND_RPC_CLIENT,
    }, child_of=get_current_span()) as span:
        headers = {}
        tracer.inject(span, Format.HTTP_HEADERS, headers)

        try:
            response = requests.get(url, headers=headers)
            return HttpResponse(response.content)
        except six.moves.urllib.error.URLError as e:
            span.set_tag(tags.ERROR, True)
            return HttpResponse("Error: " + str(e))
