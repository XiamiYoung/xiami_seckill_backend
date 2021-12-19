from django.apps import AppConfig
import os
import threading
import time
import random

from .src.config.config import global_config
from .src.utils.emailer import Emailer

from .src.utils.util import (
    str_to_json,
    get_now_datetime,
    get_timestamp_in_milli_sec,
    get_sys_info,
    get_server_uptime
)

from .src.config.constants import (
    SYS_INFO_CACHE_KEY
)

class XiamiSeckillAppConfig(AppConfig):
    name = 'xiami_seckill_backend'

    def ready(self):
        is_django_startup = os.environ.get('DJANGO_START_UP') 
        if is_django_startup is None:
            os.environ['DJANGO_START_UP'] = 'True' 

            default_system_emailer_address = global_config.get('config', 'default_system_emailer_address')
            default_system_emailer_token = global_config.get('config', 'default_system_emailer_token')
            system_emailer = Emailer(None, default_system_emailer_address, default_system_emailer_token)

            self.execute_in_thread(self.query_arrangement_on_ready, [system_emailer])
            self.execute_in_thread(self.query_sys_info_on_ready, [system_emailer])
        else:
            print('略过启动程序')
            return

    def execute_in_thread(self, func, args):
        t = threading.Thread(target=func, args=args)
        t.daemon = True
        t.start()


    def query_sys_info_on_ready(self, system_emailer):
        from .src.daos.cache.redis import CacheDao
        cache_dao = CacheDao()

        mem_threashold = 90
        gether_info_interval = 5
        notification_interval = 360 # 30 mins
        notification_count = 0

        print('开始获取系统信息')

        while True:
            sys_info = get_sys_info()
            up_time = get_server_uptime()
            cache_obj = {
                'sys_info': sys_info,
                'up_time': up_time
            }
            cache_dao.put(SYS_INFO_CACHE_KEY, cache_obj)

            mem_percent = float(sys_info['used_memory_percent'])

            if mem_percent > float(mem_threashold):
                if notification_count % notification_interval == 0:
                    system_emailer.send(subject='内存利用率:' + str(mem_percent), content='内存利用率:' + str(mem_percent))
                notification_count = notification_count + 1

            time.sleep(gether_info_interval)

    def query_arrangement_on_ready(self, system_emailer):

        # wait for db/cache startup
        time.sleep(10)

        print('正在检查是否需要继续抢购')

        from .src.services.public.jd.jd_user_service import JDUserService
        from .src.services.public.common.login_user_service import LoginUserService
        from .src.services.public.jd.jd_seckill_service import JDSeckillService

        try:
            login_user_service = LoginUserService()
            jd_user_service = JDUserService()

            login_user_list = login_user_service.find_all_users()

            for user in login_user_list:
                login_username = user['username']
                jd_user_arrangement = jd_user_service.find_jd_user_arrangement_by_username(login_username)

                # {
                #     "樱淇amy": [],
                #     "tina_wj": [
                #         {
                #         "startTime": "2021-12-18 10:00:00.000",
                #         "startTimeMills": 1639792800000,
                #         "status": "计划",
                #         "leading_time": "70",
                #         "skus": [
                #             {
                #             "skuId": "100021870666",
                #             "count": 1,
                #             "shortWname": "清风(APP)抽纸 young系列4层9..."
                #             }
                #         ]
                #         }
                #     ],
                #     "薛军xj": [],
                #     "张荣新2384": [],
                #     "吴殿清": [],
                #     "大大大大大大虾米": [
                #         {
                #         "startTime": "2021-12-18 10:00:00.000",
                #         "startTimeMills": 1639792800000,
                #         "status": "终止",
                #         "leading_time": "90",
                #         "skus": [
                #             {
                #             "skuId": "100021870666",
                #             "count": 1,
                #             "shortWname": "清风(APP)抽纸 young系列4层9..."
                #             }
                #         ],
                #         "failure_msg": ""
                #         }
                #     ]
                #     }

                # def execute_arrangement(self, execution_arrangement_array, login_username, nick_name, leading_time):
                # [{'sku_id': '10041958286026', 'num': 1, 'target_time': '2021-12-17 22:00:00.000'}, {'sku_id': '100021870666', 'num': 1, 'target_time': '2021-12-18 10:00:00.000'}]


                if jd_user_arrangement:
                    jd_user_arrangement = str_to_json(jd_user_arrangement['seckill_arrangement'])
                    leading_time = None
                    for (jd_username, arrangement_array) in jd_user_arrangement.items():
                        execution_arrangement_array = []
                        should_run_for_user = False
                        for item in arrangement_array:
                            execution_arrangement_item = {}
                            # check if expired
                            startTimeMills = item['startTimeMills']
                            now_ts = get_timestamp_in_milli_sec(get_now_datetime())
                            if now_ts >= startTimeMills:
                                continue

                            status = item['status']
                            if status == '运行':
                                should_run_for_user = True

                            start_time_str = item['startTime']
                            if not leading_time:
                                leading_time = item['leading_time']
                            skus = item['skus']
                            if not skus or len(skus)==0:
                                continue
                            
                            sku_id = skus[0]['skuId']
                            num = skus[0]['count']

                            execution_arrangement_item['sku_id'] = sku_id
                            execution_arrangement_item['num'] = num
                            execution_arrangement_item['target_time'] = start_time_str
                            
                            execution_arrangement_array.append(execution_arrangement_item)

                        if should_run_for_user:
                            print('正在恢复抢购进程: ' + jd_username)
                            jd_seckill_service = JDSeckillService(login_username)
                            jd_user = jd_user_service.find_jd_user_by_username_and_nick_name(login_username, jd_username, is_mask_jd_pwd=False)
                            if jd_user['pc_cookie_str']:
                                jd_seckill_service._assign_cookies_from_remote(jd_user['pc_cookie_str'])
                            if jd_user['mobile_cookie_str']:
                                jd_seckill_service._assign_cookies_from_remote(jd_user['mobile_cookie_str'])

                            jd_seckill_service.set_user_props(jd_user)

                            # 等待随机秒，避免cookie错误
                            random_wait = random.randint(1, 20)
                            time.sleep(random_wait)
                            self.execute_in_thread(jd_seckill_service.execute_arrangement, (execution_arrangement_array,login_username, jd_username, leading_time, True))
                        else:
                            print('用户:' + jd_username + '无需恢复抢购进程')
        except Exception as e:
            system_emailer.send(subject='重启线程失败', content='重启线程失败')