from django.http import JsonResponse
import traceback
from config.error_dict import error_dict
from utils.util import (
    is_class_type_of
)

from config.constants import (
    HTTP_CODE_500
)

class ErrorHandlerMiddleware(object):

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response

    def process_exception(self, request, exception):
        response_body = {}
        status_code = HTTP_CODE_500
        if exception:
            if is_class_type_of(exception, 'RestfulException'):
                response_body = {
                    'reasonCode': exception.reason_code,
                    'msg': exception.msg
                }
                status_code = exception.http_code
            else:
                response_body = {
                    'reasonCode': error_dict['COMMON']['DEFAULT_ERROR']['reasonCode'],
                    'msg': str(exception)
                }
                status_code = HTTP_CODE_500

        print(traceback.format_exc())
        response = JsonResponse(response_body)
        response.status_code = status_code
        return response
