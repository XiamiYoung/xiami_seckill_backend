from controllers.base.base_controller import BaseController
from config.constants import (
    JD_PC_COOKIE_NAME,
    JD_MOBILE_COOKIE_NAME,
    JWT_HEADER_USER_NAME
)
from services.public.jd.jd_order_service import JDService
from services.public.common.user_service import UserService

class JDBaseController(BaseController):
    def _get_jd_service(self):
        return JDService()

    def _get_user_service(self):
        return UserService()

    def _get_jd_service_with_cookie(self,request):
        jd_service = self._get_jd_service()
        if JD_PC_COOKIE_NAME in request.headers:
            jd_cookies = request.headers[JD_PC_COOKIE_NAME]
            self.assign_cookies_from_remote(jd_service, jd_cookies)
        if JD_MOBILE_COOKIE_NAME in request.headers:
            jd_cookies = request.headers[JD_MOBILE_COOKIE_NAME]
            self.assign_cookies_from_remote(jd_service, jd_cookies)
        return jd_service

    def _add_jd_pc_cookies_to_response_header(self,httpResponse, jd_cookies):
        httpResponse[JD_PC_COOKIE_NAME] = jd_cookies

    def _add_jd_mobile_cookies_to_response_header(self,httpResponse, jd_cookies):
        httpResponse[JD_MOBILE_COOKIE_NAME] = jd_cookies

    def assign_cookies_from_remote(self, jd_service, jd_cookies):
        jd_service._assign_cookies_from_remote(jd_cookies)

    def _get_jd_service_with_cookie_after_login(self, request, nick_name):
        user_service = self._get_user_service()
        jd_service = self._get_jd_service()
        login_user_name = self._get_login_username(request)
        pc_cookie, mobile_cookie = user_service.find_jd_user_cookies_by_username_and_nick_name(login_user_name, nick_name)
        if pc_cookie:
            jd_service._assign_cookies_from_remote(pc_cookie)
        if mobile_cookie:
            jd_service._assign_cookies_from_remote(mobile_cookie)
        return jd_service

    def _get_login_username(self, request):
        return request.headers[JWT_HEADER_USER_NAME]