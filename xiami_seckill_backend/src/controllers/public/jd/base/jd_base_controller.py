from controllers.base.base_controller import BaseController
from config.constants import (
    JD_PC_COOKIE_NAME,
    JD_MOBILE_COOKIE_NAME,
    JWT_HEADER_USER_NAME
)
from services.public.jd.jd_seckill_service import JDSeckillService
from services.public.common.login_user_service import LoginUserService
from services.public.jd.jd_order_service import JDOrderService
from services.public.jd.jd_user_service import JDUserService
from services.public.jd.jd_log_service import JDLogService

class JDBaseController(BaseController):
    def _get_jd_seckill_service(self, login_user_name):
        jd_seckill_service = JDSeckillService(login_user_name)
        return jd_seckill_service

    def _get_login_user_service(self):
        return LoginUserService()

    def _get_log_service(self):
        return JDLogService()

    def _get_jd_user_service(self):
        return JDUserService()

    def _get_jd_order_service(self):
        return JDOrderService()

    def _get_jd_seckill_service_with_cookie(self,request):
        login_user_name = self._get_login_username(request)
        jd_seckill_service = self._get_jd_seckill_service(login_user_name)
        if JD_PC_COOKIE_NAME in request.headers:
            jd_cookies = request.headers[JD_PC_COOKIE_NAME]
            self.assign_cookies_from_remote(jd_seckill_service, jd_cookies)
        if JD_MOBILE_COOKIE_NAME in request.headers:
            jd_cookies = request.headers[JD_MOBILE_COOKIE_NAME]
            self.assign_cookies_from_remote(jd_seckill_service, jd_cookies)
        return jd_seckill_service

    def _add_jd_pc_cookies_to_response_header(self,httpResponse, jd_cookies):
        httpResponse[JD_PC_COOKIE_NAME] = jd_cookies

    def _add_jd_mobile_cookies_to_response_header(self,httpResponse, jd_cookies):
        httpResponse[JD_MOBILE_COOKIE_NAME] = jd_cookies

    def assign_cookies_from_remote(self, jd_seckill_service, jd_cookies):
        jd_seckill_service._assign_cookies_from_remote(jd_cookies)

    def _get_jd_seckill_service_with_cookie_after_login(self, request, nick_name):
        login_user_name = self._get_login_username(request)
        jd_user_service = self._get_jd_user_service()
        jd_seckill_service = self._get_jd_seckill_service(login_user_name)
        jd_user = jd_user_service.find_jd_user_by_username_and_nick_name(login_user_name, nick_name, is_mask_jd_pwd=False)
        if jd_user['pc_cookie_str']:
            jd_seckill_service._assign_cookies_from_remote(jd_user['pc_cookie_str'])
        if jd_user['mobile_cookie_str']:
            jd_seckill_service._assign_cookies_from_remote(jd_user['mobile_cookie_str'])
        jd_seckill_service.set_user_props(jd_user)
        return jd_seckill_service

    def _get_login_username(self, request):
        return request.headers[JWT_HEADER_USER_NAME]