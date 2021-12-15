"""xiami_seckill_backend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from .src.controllers.public.jd.jd_controller import JDController
from .src.controllers.public.common import login_user_controller
from .src.controllers.site_admin import site_admin_controller

jd_controller = JDController()

urlpatterns = [
    path('admin/', admin.site.urls),
    path('site/login', login_user_controller.login_with_username_password),
    path('site-admin/user/create', site_admin_controller.create_enduser),
    path('site-admin/sys-info', site_admin_controller.get_sys_info),
    path('site-admin/check-sys-status', site_admin_controller.check_sys_status),
    path('site-admin/reboot-server', site_admin_controller.reboot_server),
    path('site/jd/batch-load-seckill', jd_controller.batch_load_seckill),
    path('site/jd/load-qr-code', jd_controller.check_qr_code),
    path('site/jd/wait-user-scan-qr', jd_controller.wait_user_scan_qr),
    path('site/jd/get-associated-jd-users', jd_controller.get_associated_jd_users),
    path('site/jd/check-qr-scan-result', jd_controller.check_qr_scan_result),
    path('site/jd/cancel-qr-scan-result', jd_controller.cancel_check_qr_code),
    path('site/jd/cancel-qq-qr', jd_controller.cancel_qq_qr_result),
    path('site/jd/delete-jd-user', jd_controller.delete_jd_user),
    path('site/jd/get-qq-image', jd_controller.get_qq_qr_code),
    path('site/jd/check-mobile-qr-result', jd_controller.check_mobile_qr_result),
    path('site/jd/check-qq-qr-url-result', jd_controller.check_qq_qr_url_result),
    path('site/jd/submit-security-code', jd_controller.submit_user_security_code),
    path('site/jd/start-arrangement', jd_controller.start_arrangement),
    path('site/jd/add-or-remove-arrangement', jd_controller.add_or_remove_arrangement),
    path('site/jd/cancel-arrangement', jd_controller.cancel_arrangement),
    path('site/jd/get-arrangement-status', jd_controller.get_arrangement_status),
    path('site/jd/delete-arrangement-item', jd_controller.delete_arrangement_item),
    path('site/jd/read-execution-log', jd_controller.read_execution_log),
    path('site/jd/get-jd-orders', jd_controller.get_jd_orders),
    path('site/jd/delete-jd-order', jd_controller.delete_jd_order),
    path('site/jd/cancel-jd-order', jd_controller.cancel_jd_order),
    path('site/jd/get-jd-user-arrangement', jd_controller.get_jd_user_arrangement),
    path('site/jd/save-jd-user-arrangement', jd_controller.save_jd_user_arrangement),
    path('site/jd/save-jd-user-mobile', jd_controller.save_jd_user_mobile),
    path('site/jd/save-jd-user-leading-time', jd_controller.save_jd_user_leading_time),
    path('site/jd/save-jd-user-pwd', jd_controller.save_jd_user_pwd),
    path('site/jd/save-jd-user-push-token', jd_controller.save_jd_user_push_token),
    path('site/jd/save-jd-user-push-email', jd_controller.save_jd_user_push_email),
    path('site/jd/save-jd-user-enabled', jd_controller.save_jd_user_enabled),
    path('site/jd/get-sku-by-id', jd_controller.get_sku_by_id),
    path('site/jd/add-custom-sku', jd_controller.add_custom_sku_info_to_cache),
    path('site/jd/get-custom-sku', jd_controller.get_custom_sku_data),
    path('site/jd/delete-custom-sku', jd_controller.delete_custom_sku_info_from_cache),
    path('site/jd/get-user-address', jd_controller.get_jd_user_address),
    path('site/jd/save-user-address', jd_controller.save_jd_user_address),
]
