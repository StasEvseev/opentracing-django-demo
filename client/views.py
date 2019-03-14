from django.http import HttpResponse
import aiohttp

from opentracing.ext import tags
from de.services.digitalengine.conf import settings as de_settings
from de.services.conf import settings as de_conf_settings
import redis
from django.contrib.auth.models import User

from django.db.transaction import atomic
from django.conf import settings

from jaeger_tracing_intro.client import FixedOrderService

tracer = settings.TRACER

client = redis.StrictRedis(host='host.docker.internal')

de_settings.configure(
    SERVICE_DE_BASE_LOCATION="http://uwsgi:8080"
)
de_conf_settings.configure(
    MOCK_LIBRARY=None
)


def client_index(request):
    with tracer.tracer.start_span('test') as span:
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
    # url = "http://uwsgi:8080/fixed/v1/order/"

    client.set('last_access', 'testvalue')

    with atomic():
        c = User.objects.count()
        print(c)

    service = FixedOrderService()
    response = service.get_status(customer_id=None)()

    return HttpResponse(response.raw_response)
