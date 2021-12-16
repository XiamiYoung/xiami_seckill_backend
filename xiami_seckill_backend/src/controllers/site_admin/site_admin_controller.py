from django.http import JsonResponse
from data.out.base_res_body import BaseResBody
import json
from django.views.decorators.csrf import csrf_exempt
from controllers.base.base_controller import BaseController
from services.site_admin.site_admin_service import SiteAdminService

from utils.util import (
    str_to_json
)

site_admin_service = SiteAdminService()

class SiteAdminController(BaseController):

    @csrf_exempt
    def create_enduser(self, request):

        # read data as json
        data = json.loads(request.body)

        # call service
        ret_data = site_admin_service.create_enduser(data)

        # resp
        resp_body = BaseResBody().to_json_body()
        resp_body['body'] = ret_data
        return JsonResponse(resp_body)

    @csrf_exempt
    def get_sys_info(self, request):

        # call service
        ret_data = site_admin_service.check_sys_info_result()

        # resp
        resp_body = BaseResBody().to_json_body()
        resp_body['body'] = ret_data
        return JsonResponse(resp_body)

    @csrf_exempt
    def trigger_sys_info(self, request):

        # call service in thread
        self.execute_in_thread(site_admin_service.trigger_sys_info, ())

        # resp
        resp_body_data = {
                            'executed':True
                        }
        resp_body = BaseResBody().to_json_body()
        resp_body['body'] = resp_body_data
        return JsonResponse(resp_body)

    @csrf_exempt
    def reboot_server(self, request):

        # call service
        ret_data = site_admin_service.reboot_server()

        # resp
        resp_body = BaseResBody().to_json_body()
        resp_body['body'] = ret_data
        return JsonResponse(resp_body)

    @csrf_exempt
    def find_all_users(self, request):
        # read data as json
        data = str_to_json(request.body)
        username = ''
        if 'username' in data:
            username = data['username']

        # call service
        ret_data = site_admin_service.find_all_users(username=username, with_order=True)

        # resp
        resp_body = BaseResBody().to_json_body()
        resp_body['body'] = ret_data
        return JsonResponse(resp_body)
