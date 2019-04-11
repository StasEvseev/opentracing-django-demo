from de.services.digitalengine.fixed.order.client import FixedOrderService
from de.services.conf import settings
from django.http import HttpResponse

import aiohttp

from opentracing.ext import tags
from de.services.digitalengine.conf import settings as de_settings
from de.services.conf import settings as de_conf_settings
from de.core.conf import settings as de_core_settings
import redis
from django.contrib.auth.models import User

from django.db.transaction import atomic

client = redis.StrictRedis(host='host.docker.internal')

de_settings.configure(
    SERVICE_DE_BASE_LOCATION="http://uwsgi:8080"
)
de_conf_settings.configure(
    MOCK_LIBRARY=None
)

de_core_settings.configure(
    JAEGER_ENABLED=True
)


def client_index(request):
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
    #: our journey start here
    client.set('last_access', 'testvalue')

    with atomic():
        User.objects.count()

    service = FixedOrderService()
    response = service.get_status(customer_id=None)()

    service.save(params={})()
    service.update(params={})()

    return HttpResponse(response.raw_response)
