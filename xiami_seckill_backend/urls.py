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
from .src.controllers.public.common import user_controller
from .src.controllers.site_admin import site_admin_controller

jd_controller = JDController()

urlpatterns = [
    path('admin/', admin.site.urls),
    path('site/login', user_controller.login_with_username_password),
    path('site/batch_load_seckill', jd_controller.batch_load_seckill),
    path('site-admin/user/create', site_admin_controller.create_enduser),
    path('site/jd/load-qr-code', jd_controller.check_qr_code),
    path('site/jd/wait-user-scan-qr', jd_controller.wait_user_scan_qr),
    path('site/jd/get-associated-jd-users', jd_controller.get_associated_jd_users),
    path('site/jd/check-qr-scan-result', jd_controller.check_qr_scan_result),
    path('site/jd/cancel-qr-scan-result', jd_controller.cancel_check_qr_code),
    path('site/jd/cancel-user-mobile-code-input', jd_controller.cancel_user_inpu_mobile_code),
    path('site/jd/delete-jd-user', jd_controller.delete_jd_user),
    path('site/jd/submit-mobile-code', jd_controller.submit_user_mobile_code),
    path('site/jd/send-mobile-code', jd_controller.send_mobile_code),
    path('site/jd/check-mobile-code-result', jd_controller.check_mobile_code_result),
    path('site/jd/start-arrangement', jd_controller.start_arrangement),
    path('site/jd/add-or-remove-arrangement', jd_controller.add_or_remove_arrangement),
    path('site/jd/cancel-arrangement', jd_controller.cancel_arrangement),
    path('site/jd/get-arrangement-status', jd_controller.get_arrangement_status),
    path('site/jd/delete-arrangement-item', jd_controller.delete_arrangement_item),
    path('site/jd/read-execution-log', jd_controller.read_execution_log),
    path('site/jd/get-jd-orders', jd_controller.get_jd_orders),
    path('site/jd/cancel-jd-order', jd_controller.cancel_jd_order),
]
