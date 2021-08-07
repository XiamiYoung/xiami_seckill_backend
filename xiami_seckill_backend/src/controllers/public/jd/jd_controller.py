from django.http import JsonResponse
from django.http import HttpResponse
from data.out.base_res_body import BaseResBody
from django.views.decorators.csrf import csrf_exempt
from controllers.public.jd.base.jd_base_controller import JDBaseController
from utils.util import (
    str_to_json
)

class JDController(JDBaseController):

    @csrf_exempt
    def check_qr_code(self, request):
        # get JD service
        jd_service = self._get_jd_service_with_cookie(request)

        # get QR code
        qr_code_response, cookie_token, jd_cookies = jd_service.load_QRcode()

        # send response
        response= HttpResponse(qr_code_response, content_type='image/png')
        response['cookie-token'] = cookie_token
        # add cookies
        self._add_jd_pc_cookies_to_response_header(response, jd_cookies)

        return response

    @csrf_exempt
    def cancel_check_qr_code(self, request):
        # read data as json
        data = str_to_json(request.body)
        cookie_token = data['cookie-token']

        # get JD service
        jd_service = self._get_jd_service_with_cookie(request)

        # cancel qr code scan
        ret = jd_service.cancel_qr_scan(cookie_token)

        # send response
        resp_body = BaseResBody().to_json_body()
        resp_body_data = {
                            'success': True,
                            'ret':ret
                         }
        resp_body['body'] = resp_body_data
        response = JsonResponse(resp_body)

        return response

    @csrf_exempt
    def cancel_user_inpu_mobile_code(self, request):
        # read data as json
        data = str_to_json(request.body)
        nick_name = data['nick_name']
        login_username = self._get_login_username(request)

        # get JD service
        jd_service = self._get_jd_service_with_cookie(request)

        # cancel qr code scan
        ret = jd_service.cancel_mobile_code_input(login_username, nick_name)

        # send response
        resp_body = BaseResBody().to_json_body()
        resp_body_data = {
                            'success': True,
                            'ret':ret
                         }
        resp_body['body'] = resp_body_data
        response = JsonResponse(resp_body)

        return response

    @csrf_exempt
    def check_qr_scan_result(self, request):
        # read data as json
        data = str_to_json(request.body)
        cookie_token = data['cookie-token']

        # get JD service
        jd_service = self._get_jd_service_with_cookie(request)  
        result = jd_service.check_qr_scan_result(cookie_token)

        resp_body_data = {
                            'success': False
                        }

        # send response
        resp_body = BaseResBody().to_json_body()
        if result and 'success' in result and result['success']:
            jd_user_data = result['jd_user_data']

            resp_body_data = {
                                'success': True,
                                'jd_user_data':jd_user_data
                            }
            resp_body['body'] = resp_body_data
            response = JsonResponse(resp_body)
        else:
            resp_body['body'] = resp_body_data
            response = JsonResponse(resp_body)

        return response

    @csrf_exempt
    def wait_user_scan_qr(self, request):
        # read data as json
        data = str_to_json(request.body)
        cookie_token = data['cookie-token']
        login_username = self._get_login_username(request)

        # get JD service
        jd_service = self._get_jd_service_with_cookie(request) 

        # call login service
        self.execute_in_thread(jd_service.load_login_cookie, (login_username, cookie_token))

        # send response
        resp_body = BaseResBody().to_json_body()
        resp_body_data = {
                            'executed':True
                        }
        resp_body['body'] = resp_body_data
        response = JsonResponse(resp_body)

        return response

    @csrf_exempt
    def get_associated_jd_users(self, request):
        login_username = self._get_login_username(request)

        # call service
        resp_json =  self._get_user_service().find_user_by_username(login_username, is_return_model=True)

        # remove unwanted attrs
        jd_user_list = list(resp_json.jduser_set.all().values())
        for item in jd_user_list:
            item['pc_cookie_str'] = ''
            item['mobile_cookie_str'] = ''
            item['created_ts'] = ''
            item['updated_ts'] = ''
            
        # send response
        resp_body_data = {
                            'success': True,
                            'jd_users': jd_user_list
                        }
        resp_body = BaseResBody().to_json_body()
        resp_body['body'] = resp_body_data
        response = JsonResponse(resp_body)
        
        return response

    @csrf_exempt
    def delete_jd_user(self, request):
        data = str_to_json(request.body)
        nick_name = data['nick_name']
        login_username = self._get_login_username(request)

        # call service
        self._get_jd_service().delete_arrangement_item(login_username, nick_name)
        self._get_user_service().delete_jd_user_by_nick_name(login_username, nick_name)

        # send response
        resp_body_data = {
                            'success': True,
                        }
        resp_body = BaseResBody().to_json_body()
        resp_body['body'] = resp_body_data
        response = JsonResponse(resp_body)
        
        return response

    @csrf_exempt
    def submit_user_mobile_code(self, request):
        # read data as json
        data = str_to_json(request.body)
        nick_name = data['nick_name']
        mobile_code = data['mobile_code']
        login_username = self._get_login_username(request)

        # get JD service
        jd_service = self._get_jd_service() 

        # call login service
        jd_service.put_user_input_mobile_code(login_username, nick_name, mobile_code)

        # send response
        resp_body = BaseResBody().to_json_body()
        resp_body_data = {
                            'executed':True
                        }
        resp_body['body'] = resp_body_data
        response = JsonResponse(resp_body)

        return response

    @csrf_exempt
    def send_mobile_code(self, request):
        # read data as json
        data = str_to_json(request.body)
        nick_name = data['nick_name']
        mobile = data['mobile']
        login_username = self._get_login_username(request)

        # get JD service
        jd_service = self._get_jd_service() 

        # call login service
        self.execute_in_thread(jd_service.mobile_login, (login_username, nick_name, mobile))

        # send response
        resp_body = BaseResBody().to_json_body()
        resp_body_data = {
                            'executed':True
                        }
        resp_body['body'] = resp_body_data
        response = JsonResponse(resp_body)

        return response

    @csrf_exempt
    def check_mobile_code_result(self, request):
        # read data as json
        data = str_to_json(request.body)
        nick_name = data['nick_name']
        login_username = self._get_login_username(request)

        # get JD service
        jd_service = self._get_jd_service()  
        result = jd_service.check_mobile_code_result(login_username, nick_name)

        resp_body_data = {
                            'success': False
                        }

        # send response
        resp_body = BaseResBody().to_json_body()
        if result and 'success' in result and result['success']:
            jd_user_data = result['jd_user_data']

            # remove unwanted attrs
            jd_user_data['pc_cookie_str'] = ''
            jd_user_data['mobile_cookie_str'] = ''
            jd_user_data['created_ts'] = ''
            jd_user_data['updated_ts'] = ''

            resp_body_data = {
                                'success': True,
                                'jd_user_data':jd_user_data
                            }
            resp_body['body'] = resp_body_data
            response = JsonResponse(resp_body)
        elif result and 'success' in result and not result['success']:
            resp_body_data = {
                                'success': False,
                                'error':result['msg']
                            }
            resp_body['body'] = resp_body_data
            response = JsonResponse(resp_body)    
        else:
            resp_body['body'] = resp_body_data
            response = JsonResponse(resp_body)

        return response

    @csrf_exempt
    def batch_load_seckill(self, request):
        data = str_to_json(request.body)
        is_force_refresh = data['is_force_refresh']
        # get JD service
        jd_service = self._get_jd_service() 

        # call service
        resp_json =  jd_service.batch_load_seckill(is_force_refresh)

        # send response
        resp_body = BaseResBody().to_json_body()
        resp_body['body'] = resp_json
        response = JsonResponse(resp_body)
        
        return response

    @csrf_exempt
    def get_sku_by_id(self, request):
        # get data
        data = str_to_json(request.body)
        sku_id = data['sku_id']

        # get JD service
        jd_service = self._get_jd_service()

        resp_body = BaseResBody().to_json_body()

        # call service
        try:
            ret = jd_service.get_item_detail_info(sku_id, is_wait_for_limit=True)
            resp_body_data = {
                                'success': True,
                                'sku_data': ret
                            }
        except Exception as e:
            resp_body_data = {
                                'success': False,
                                'error': "读取商品信息失败"
                            }
        # send response
        resp_body['body'] = resp_body_data
        response = JsonResponse(resp_body)
        return response


    @csrf_exempt
    def start_arrangement(self, request):
        # get data
        data = str_to_json(request.body)
        arrangement_list = data['arrangement_list']
        nick_name = data['nick_name']
        leading_time = data['leading_time']
        login_username = self._get_login_username(request)

        # get JD service
        jd_service = self._get_jd_service_with_cookie_after_login(request, nick_name) 

        execution_arrangement_array = []
        for item in arrangement_list:
            skus = item['skus']
            for sku in skus:
                execution_item = {
                    'sku_id': sku['skuId'],
                    'num': sku['count'],
                    'target_time': item['startTime']
                }
                execution_arrangement_array.append(execution_item)

        # call service
        self.execute_in_thread(jd_service.execute_arrangement, (execution_arrangement_array,login_username, nick_name, leading_time))

        # send response
        resp_body = BaseResBody().to_json_body()
        resp_body_data = {
                            'executed':True
                        }
        resp_body['body'] = resp_body_data
        response = JsonResponse(resp_body)
        return response

    @csrf_exempt
    def cancel_arrangement(self, request):
        # get data
        data = str_to_json(request.body)
        arrangement_list = data['arrangement_list']
        nick_name = data['nick_name']
        login_username = self._get_login_username(request)

        # get JD service
        jd_service = self._get_jd_service()

        execution_arrangement_array = []
        for item in arrangement_list:
            skus = item['skus']
            for sku in skus:
                execution_item = {
                    'sku_id': sku['skuId'],
                    'num': sku['count'],
                    'target_time': item['startTime']
                }
                execution_arrangement_array.append(execution_item)

        # call service
        self.execute_in_thread(jd_service.cancel_arrangement, (execution_arrangement_array,login_username, nick_name))

        # send response
        resp_body = BaseResBody().to_json_body()
        resp_body_data = {
                            'executed':True
                        }
        resp_body['body'] = resp_body_data
        response = JsonResponse(resp_body)
        return response

    @csrf_exempt
    def add_or_remove_arrangement(self, request):
        # get data
        data = str_to_json(request.body)
        target_time = data['target_time']
        nick_name = data['nick_name']
        is_add = data['is_add']
        login_username = self._get_login_username(request)

        # get JD service
        jd_service = self._get_jd_service()

        # call service
        self.execute_in_thread(jd_service.add_or_remove_arrangement, (target_time, login_username, nick_name, is_add))

        # send response
        resp_body = BaseResBody().to_json_body()
        resp_body_data = {
                            'executed':True
                        }
        resp_body['body'] = resp_body_data
        response = JsonResponse(resp_body)
        return response

    @csrf_exempt
    def get_arrangement_status(self, request):
        # get data
        login_username = self._get_login_username(request)

        # get JD service
        jd_service = self._get_jd_service()

        # call service
        ret = jd_service.get_arrangement_status(login_username)

        # send response
        resp_body = BaseResBody().to_json_body()
        resp_body['body'] = ret
        response = JsonResponse(resp_body)
        return response

    @csrf_exempt
    def delete_arrangement_item(self, request):
        # get data
        data = str_to_json(request.body)
        target_time = data['target_time']
        nick_name = data['nick_name']
        login_username = self._get_login_username(request)

        # get JD service
        jd_service = self._get_jd_service()

        # call service
        jd_service.delete_arrangement_item(login_username, nick_name, target_time)

        # send response
        resp_body = BaseResBody().to_json_body()
        resp_body_data = {
                            'executed':True
                        }
        resp_body['body'] = resp_body_data
        response = JsonResponse(resp_body)
        return response

    @csrf_exempt
    def add_custom_sku_info_to_cache(self, request):
        # get data
        data = str_to_json(request.body)
        sku_data = data['sku_data']
        login_username = self._get_login_username(request)

        # get JD service
        jd_service = self._get_jd_service()

        # call service
        self.execute_in_thread(jd_service.add_custom_sku_info_to_cache, (login_username, sku_data))

        # send response
        resp_body = BaseResBody().to_json_body()
        resp_body_data = {
                            'executed':True
                        }
        resp_body['body'] = resp_body_data
        response = JsonResponse(resp_body)
        return response

    @csrf_exempt
    def get_custom_sku_data(self, request):
        # get data
        login_username = self._get_login_username(request)

        # get JD service
        jd_service = self._get_jd_service()

        # call service
        sku_data = jd_service.get_custom_sku_info_from_cache(login_username)

        # send response
        resp_body = BaseResBody().to_json_body()
        if sku_data:
            resp_body_data = {
                                'success': True,
                                'sku_data': sku_data
                            }
        else:
            resp_body_data = {
                                'success': False
                            }
        resp_body['body'] = resp_body_data
        response = JsonResponse(resp_body)
        return response
        
    @csrf_exempt
    def read_execution_log(self, request):
        # get data
        data = str_to_json(request.body)
        nick_name = data['nick_name']
        last_id = data['last_id']
        login_username = self._get_login_username(request)

        # get JD service
        jd_service = self._get_jd_service() 

        # call service
        ret = jd_service.read_execution_log(login_username, nick_name, last_id)

        # send response
        resp_body = BaseResBody().to_json_body()
        resp_body['body'] = ret
        response = JsonResponse(resp_body)
        return response

    @csrf_exempt
    def get_jd_orders(self, request):
        login_username = self._get_login_username(request)

        # get JD service
        user_service = self._get_user_service()  
        jd_order_list = user_service.find_jd_orders_by_username(login_username)

        # send response
        resp_body = BaseResBody().to_json_body()
        resp_body_data = {
                            'success': True,
                            'jd_order_list': jd_order_list
                        }
        resp_body['body'] = resp_body_data
        response = JsonResponse(resp_body)

        return response

    @csrf_exempt
    def cancel_jd_order(self, request):
        data = str_to_json(request.body)
        order_id = data['order_id']
        nick_name = data['nick_name']

        # get JD service
        jd_service = self._get_jd_service_with_cookie_after_login(request, nick_name) 

        resp_body = BaseResBody().to_json_body()

        # check cookie valid
        if not jd_service.get_user_info():
            resp_body_data = {
                            'success': False,
                            'msg': '用户cookie失效'
                        }
            resp_body['body'] = resp_body_data
            response = JsonResponse(resp_body)
            return response

        # get JD service
        result, msg = jd_service.cancel_order(order_id)

        # send response
        
        resp_body_data = {
                            'success': result,
                            'msg': msg
                        }
        resp_body['body'] = resp_body_data
        response = JsonResponse(resp_body)

        return response

    @csrf_exempt
    def save_jd_user_arrangement(self, request):
        # get data
        data = str_to_json(request.body)
        user_arrangement = data['user_arrangement']
        login_username = self._get_login_username(request)

        # get JD User service
        user_service = self._get_user_service()  

        # call service
        self.execute_in_thread(user_service.save_or_update_jd_user_arrangement, (login_username, user_arrangement))

        # send response
        resp_body = BaseResBody().to_json_body()
        resp_body_data = {
                            'executed':True
                        }
        resp_body['body'] = resp_body_data
        response = JsonResponse(resp_body)
        return response

    @csrf_exempt
    def save_jd_user_options(self, request):
        # get data
        data = str_to_json(request.body)
        user_options = data['user_options']
        nick_name = data['nick_name']

        # get JD User service
        user_service = self._get_user_service()  

        # call service
        if 'leading_time' in user_options:
            self.execute_in_thread(user_service.update_leading_time, (nick_name, user_options['leading_time']))

        # send response
        resp_body = BaseResBody().to_json_body()
        resp_body_data = {
                            'executed':True
                        }
        resp_body['body'] = resp_body_data
        response = JsonResponse(resp_body)
        return response

    @csrf_exempt
    def get_jd_user_arrangement(self, request):
        login_username = self._get_login_username(request)

        # get JD service
        user_service = self._get_user_service()  
        jd_user_arrangement = user_service.find_jd_user_arrangement_by_username(login_username)

        # send response
        resp_body = BaseResBody().to_json_body()

        if jd_user_arrangement:
            resp_body_data = {
                                'success': True,
                                'user_arrangement': {
                                    'seckill_arrangement': str_to_json(jd_user_arrangement['seckill_arrangement']),
                                    'sku_arrangement': str_to_json(jd_user_arrangement['sku_arrangement'])
                                }
                            }
        else:
            resp_body_data = {
                                'success': False,
                                'user_arrangement': {}
                            }
        resp_body['body'] = resp_body_data
        response = JsonResponse(resp_body)

        return response