from django.http import HttpResponse
from exception.restful_exception import RestfulException
from data.out.base_res_body import BaseResBody
from config.error_dict import error_dict
from utils.token_util import (
    get_user_name_from_token,
    validate_token,
    refresh_token
)

from config.constants import (
    JWT_HEADER_TOKEN_NAME,
    JWT_HEADER_USER_NAME,
    JWT_HEADER_TOKEN_HEADER_NAME,
    JWT_AUTHZ_TYPE,
    HTTP_CODE_401
)


class TokenAuthMiddleware(object):

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        if not path.startswith('/site/login'):
            try:
                auth_header = request.headers[JWT_HEADER_TOKEN_NAME]
                logged_in_user_header = request.headers[JWT_HEADER_USER_NAME]

                if auth_header and auth_header.startswith(JWT_AUTHZ_TYPE) and not path.endswith('logout'):
                    auth_token = auth_header[len(JWT_AUTHZ_TYPE):].strip()
                    token_username = get_user_name_from_token(auth_token)
                    if token_username:
                        validate_token(auth_token, logged_in_user_header)
                        refreshed_token = refresh_token(auth_token)
                        response = self.get_response(request)
                        response[JWT_HEADER_TOKEN_HEADER_NAME] = refreshed_token
                        response[JWT_HEADER_USER_NAME] = token_username
                        return response
                    else:
                        error_entry = error_dict['USER']['TOKEN_INVALID']
                        is_keep_body = False
                        res_body = BaseResBody(reason_code=error_entry['reasonCode'], msg=error_entry['msg']).to_str(is_keep_body)
                        response = HttpResponse(res_body, content_type = "application/json; charset=utf-8")
                        response.status_code = HTTP_CODE_401
                        response['Content-Length'] = len(res_body.encode('utf-8'))
                        return response
            except RestfulException as re:
                is_keep_body = False
                res_body = BaseResBody(re.reason_code, re.msg).to_str(is_keep_body)
                response = HttpResponse(res_body, content_type = "application/json; charset=utf-8")
                response.status_code = HTTP_CODE_401
                response['Content-Length'] = len(res_body.encode('utf-8'))
                return response
            except Exception as e:
                error_entry = error_dict['USER']['TOKEN_INVALID']
                is_keep_body = False
                res_body = BaseResBody(reason_code=error_entry['reasonCode'], msg=error_entry['msg']).to_str(is_keep_body)
                response = HttpResponse(res_body, content_type = "application/json; charset=utf-8")
                response.status_code = HTTP_CODE_401
                response['Content-Length'] = len(res_body.encode('utf-8'))
                return response
                
        response = self.get_response(request)
        return response