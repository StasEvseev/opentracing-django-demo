from __future__ import unicode_literals

from fqn_decorators import Decorator
from opentracing_instrumentation.request_context import get_current_span

from opentracing.ext import tags
from opentracing import tracer

import warnings

from fqn_decorators import Decorator
from time_execution import time_execution

from de.services.conf import settings
from de.services.dashboard.decorators import raise_for_maintenance
from de.utils import threads
from de.utils.constants import PY_35_GT


if PY_35_GT:
    from time_execution import time_execution_async
    from de.services.dashboard.decorators import raise_for_maintenance_async


def retrieve_result(obj):
    """
    An helper function that calls an object if it is a lambda function.
    """
    if callable(obj):
        warnings.warn(
            "Returning a callable (e.g. lambda) at a service call is deprecated. "
            "Instead, return the service model instance", DeprecationWarning)
        return obj()
    return obj


class JaegerDecorator(Decorator):
    def before(self):
        self.span = tracer.start_span(self.func.fqn, tags={
            tags.SPAN_KIND: tags.SPAN_KIND_RPC_CLIENT,
        }, child_of=get_current_span())

        self.span.__enter__()

    def after(self):
        self.span.finish()
        pass

    def exception(self):
        import traceback
        traceback.print_exc()


class Service(Decorator):

    def __init__(self, *args, **kwargs):
        self.__applied = False
        self.__non_threaded_func = None
        super(Service, self).__init__(*args, **kwargs)

        try:
            # Assuming this is decorating a method on a
            # :class:`de.services.base_service.BaseService` instance.
            self._async = bool(self.func.__self__.loop)
        except AttributeError:
            self._async = False

    def __call__(self, *args, **kwargs):
        # XXX: This is needed to pass decorator arguments (e.g. `timeout`)
        # to the decorated function. Is there a cleaner way?
        return super(Service, self).__call__(*args, **dict(kwargs, **self.params))

    def apply_time_execution(self):
        decorator = time_execution if not self._async else time_execution_async
        self.func = decorator(self.func)
        self.func.fqn = self.fqn

    def apply_raise_for_maintenance(self):
        decorator = raise_for_maintenance if not self._async else raise_for_maintenance_async
        self.func = decorator(self.func)
        self.func.fqn = self.fqn

    def apply_callable_resolver(self):
        self.func = CallableResolver(self.func)
        self.func.fqn = self.fqn

    def apply_threading(self):
        if self.kwargs.get('threaded'):
            self.threaded = True
            # Removing argument threaded from kwargs, since threading is handled by the decorator.
            self.kwargs['threaded'] = False

            timeout = self.params.get('timeout')
            if not timeout:
                # Get timeout from the service instance object
                # the decorator (self) is bound to an object available in self.__self__
                timeout = getattr(self.__self__, 'timeout', settings.SERVICE_TIMEOUT)

            wrapped_func = threads.threaded(
                self.func,
                log_exceptions=False,
                # get timeout from the service instance object
                timeout=timeout,
                raise_for_timeout=True)

            self.func = lambda *args, **kwargs: wrapped_func(*args, **kwargs)
        else:
            self.threaded = False
            wrapped_func = self.func
            # we also wrap in a lambda to make sure self.func has the same
            # interface.
            self.func = lambda *args, **kwargs: wrapped_func(*args, **kwargs)

    def before(self):
        if not self.__applied:
            if self._async:
                # NOTE: This decorator should be applied first (thus it will be
                # called last), and it's only meant for async usage.
                self.apply_callable_resolver()
            self.apply_raise_for_maintenance()
            self.apply_time_execution()
            self.func = JaegerDecorator(self.func)

        self.__applied = True

        if not self._async:
            self.__non_threaded_func = self.func
            self.apply_threading()

    def after(self):
        if not self._async:
            # Restore the function to ensure threading can be enabled and disabled
            # on subsequent calls
            self.func = self.__non_threaded_func

            if self.threaded:
                returned_value = self.result
                # We return a lambda function that ultimately will join the thread
                # Any exceptions from the thread will be raised at the join.
                self.result = lambda: retrieve_result(returned_value.result)


my_service = Service


class CallableResolver(Decorator):
    """Decorator to resolve callable service method results

    Background: according to our `service package development guidelines`_,
    service methods must return a response model wrapped in a lambda (or any
    callable).

    This becomes a problem for async usage, since the user code should always
    get an awaitable object for it to resolve, but with the lambda response
    this awaitable gets split into two: the coroutine from the async decorators
    (time_execution, raise_for_maintenance, etc.), and the actual HTTP call
    coroutine, which needs to be awaited on by the service response model:

        +------------------+                   +-------------+
        |                  |                   |             |
        | Async decorators +-----> lambda ---->+  HTTP call  |
        |    coroutine     |                   |  coroutine  |
        |                  |                   |             |
        +------------------+                   +-------------+

    In order to effectively "join" these coroutines, we ensure that the only
    non-awaitable component here (the lambda/callable) is resolved *before*
    it reaches user code, thus simplifying the user API to a single ``await``.

    I.e. without this Callable Resolver, the user code would require two
    ``await``s and would look something like:

        # await on the async decorators coroutine
        result = await http_service.service_method()
        # resolve the lambda, and await on the HTTP call coroutine
        response_model = await result()

    Whereas with the Callable Resolver the API becomes much simpler:

        response_model = await http_service.service_method()


    This decorator *MUST* be executed as the last step for async service usage.
    It's not as useful for sync + non-threaded usage, since the lambda can
    easily be resolved in user code, and it's actually harmful for sync +
    threaded usage since we *want* the underlying threads to be joined in user
    code.

    .. _service package development guidelines: https://confluence.kpn.org/x/jQC0AQ
    """
    def after(self):
        if callable(self.result):
            self.result = self.result()
