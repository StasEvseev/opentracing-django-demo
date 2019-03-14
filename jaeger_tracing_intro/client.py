from de.services.decorators import service

from de.services.digitalengine.fixed.order import models
from de.services.digitalengine.fixed.client import FixedService
from de.services.digitalengine.fixed.transformations import formatted_zip_code

from jaeger_tracing_intro.decorator import my_service


class FixedOrderService(FixedService):
    @my_service
    def get_status(self, customer_id, customer_order_number=None, bundle_id=None, address=None, threaded=False):
        """
        Client to get current order status

        Args:
            customer_id (str): the id of the customer to whom the order belongs to (L3)
            customer_order_number (str): the order identifier
            bundle_id (str): the id of the customer to whom the order belongs to (Lion)
            address (dict): the address details  to which the order is related to

        Returns:
            OrderStatusModel: the order status information

        Raises:
            InternalServerError
            BadRequestException
            BackendUnavailableException
            UnexpectedBackendResponseException
            FeatureOfflineException
            OrderNotFound
        """
        params = {'customer_id': customer_id, 'customer_order_number': customer_order_number, 'bundle_id': bundle_id}
        if address:
            params.update(
                {
                    'zip_code': formatted_zip_code(address.get('zip_code')),
                    'house_number': address.get('house_number'),
                    'house_number_extension': address.get('house_number_extension'),
                }
            )

        resource = '/v1/order/?'

        for param_key, param_value in params.items():
            if param_value:
                params_separator = '' if resource[-1] == '?' else '&'
                resource = '{previous_resource}{params_separator}{param_key}={param_value}'.format(
                    previous_resource=resource,
                    params_separator=params_separator,
                    param_key=param_key,
                    param_value=param_value,
                )

        response = self.get(self.get_client(), resource, data=params)
        return lambda: models.OrderStatusModel(response.output())

    @service
    def precheck(self, params, threaded=False):
        """
        Client for order precheck endpoint

        Args:
            params (dict):
                Example:{
                    'order_type': 'NEW',
                    'supply_chain': 'SNI',
                    'sales_channel_id': 'kpn.com telefonisch',
                    'service_address': {
                        'house_number': '111',
                        'zip_code': '1056NV'
                    },
                    'target_package_id': '2-GHGTZ9'
                }

        Returns:
            OrderPrecheckResponseModel

        Raises:
            InternalServerError
            BadRequestException
            BackendUnavailableException
            UnexpectedBackendResponseException
            FeatureOfflineException
            AddressNotFoundException
            CustomerNotFoundException
            ServiceNotFoundException
            TargetPackageIdNotFoundException
            ConfigurationErrorException
            requests.exceptions.HTTPError
        """
        resource = '/v1/order/precheck/'

        response = self.post(self.get_client(), resource, data=params)
        return lambda: models.OrderPrecheckResponseModel(response.output())

    @service
    def save(self, params, threaded=False):
        """
        Client for order precheck endpoint

        Args:
            params (dict):
                Example:{
                    'order_type': 'NEW',
                    'supply_chain': 'SNI',
                    'sales_channel_id': 'kpn.com telefonisch',
                    'service_address': {
                        'house_number': '111',
                        'zip_code': '1056NV'
                    },
                    'target_package_id': '2-GHGTZ9'
                }

        Returns:
            SaveOrderModel

        Raises:
            InternalServerError
            BadRequestException
            BackendUnavailableException
            UnexpectedBackendResponseException
            FeatureOfflineException
            OrderNotSuccessfulException
            PrecheckNotFoundException
            IncorrectTelephonyServicesException
            requests.exceptions.HTTPError
        """
        resource = '/v1/order/'

        response = self.post(self.get_client(), resource, data=params)
        return lambda: models.SaveOrderModel(response.output())

    @service
    def creditcheck(self, params, threaded=False):
        """
        Client for order creditcheck endpoint

        Args:
            params (dict):
                Example:{
                    'salesman_code': 'KPNCC',
                    'date': '2017-09-08',
                    'customer_order_type': 9,
                    'iban': IBAN('NL95ABNA0411081455'),
                    'address': {'zip_code': '1231AB'},
                }

        Returns:
            CreditCheckModel

        Raises:
            InternalServerError
            BadRequestException
            BackendUnavailableException
            UnexpectedBackendResponseException
            FeatureOfflineException
            requests.exceptions.HTTPError
        """
        resource = '/v1/order/creditcheck/'

        response = self.post(self.get_client(), resource, data=params)
        return lambda: models.CreditCheckModel(response.output())

    @service
    def update(self, params, threaded=False):
        """
        Client for order update endpoint

        Args:
            params (dict):
                Example:
                    {
                        'channel_id': '1',
                        'customer_id': '1',
                        'order_number': '1',
                        'order_reference': '1',
                        'products': [
                            {
                                'id': '1',
                                'action': 'DELETE'
                            }
                        ],
                        'engineer_service': {
                            'appointment_id': '1',
                            'slot': {
                                'date': '2017-10-17',
                                'start_time': '13:00:00',
                                'end_time': '14:00:00',
                            }
                        }
                    }

        Returns:
            UpdateOrderModel

        Raises:
            InternalServerError
            BadRequestException
            BackendUnavailableException
            UnexpectedBackendResponseException
            requests.exceptions.HTTPError
        """
        resource = '/v1/order/'
        response = self.put(self.get_client(), resource, data=params)
        return lambda: models.UpdateOrderModel(response.output())

    @service
    def get_pending_order(self, customer_id, threaded=False):
        """
        Get pending order data for a customer

        Args:
            customer_id (string): Fixed customer id

        Returns:
            PendingOrderModel

        Raises:
            InternalServerError
            BadRequestException
            BackendUnavailableException
            UnexpectedBackendResponseException
            FeatureOfflineException
            requests.exceptions.HTTPError
        """
        resource = '/v1/order/pending/?customer_id={customer_id}'.format(customer_id=customer_id)

        response = self.get(self.get_client(), resource)
        return lambda: models.PendingOrderModel(response.output())
