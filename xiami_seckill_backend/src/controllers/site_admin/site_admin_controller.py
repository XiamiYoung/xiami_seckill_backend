from django.http import JsonResponse
from data.out.base_res_body import BaseResBody
import json
from django.views.decorators.csrf import csrf_exempt
from services.site_admin.site_admin_service import SiteAdminService

site_admin_service = SiteAdminService()

@csrf_exempt
def create_enduser(request):

    # read data as json
    data = json.loads(request.body)

    # call service
    user_data = site_admin_service.create_enduser(data)

    # resp
    resp_body = BaseResBody().to_json_body()
    resp_body['body'] = user_data
    return JsonResponse(resp_body)


