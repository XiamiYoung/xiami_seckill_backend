from django.http import JsonResponse
import json
from data.out.base_res_body import BaseResBody
from django.views.decorators.csrf import csrf_exempt
from services.public.common.login_user_service import LoginUserService
from config.error_dict import error_dict
from exception.restful_exception import RestfulException
from config.constants import (
    JWT_HEADER_USER_NAME,
    JWT_HEADER_TOKEN_HEADER_NAME,
)

from utils.token_util import (
    generate_token
)

login_user_service = LoginUserService()

@csrf_exempt
def login_with_username_password(request):

    # read data as json
    data = json.loads(request.body)

    # call service
    user_data = login_user_service.login_with_username_password(data)

    if not user_data:
        raise RestfulException(error_dict['USER']['REQUEST_INVALID'])

    # resp
    resp_body = BaseResBody().to_json_body()
    resp_body['body'] = user_data

    # generate token
    username = user_data['username']
    auth_token = generate_token(username)

    json_response = JsonResponse(resp_body)
    json_response[JWT_HEADER_TOKEN_HEADER_NAME] = auth_token
    json_response[JWT_HEADER_USER_NAME] = username
    
    return json_response