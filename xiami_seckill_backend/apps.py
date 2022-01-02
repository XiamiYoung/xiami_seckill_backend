from django.apps import AppConfig
import os
import threading
import time
import random
import traceback

from .src.config.config import global_config
from .src.utils.emailer import Emailer
from .src.utils.log import Logger

from .src.utils.util import (
    str_to_json,
    str_to_datetime,
    get_now_datetime,
    get_timestamp_in_milli_sec,
    get_sys_info,
    get_server_uptime
)

from .src.config.constants import (
    SYS_INFO_CACHE_KEY,
    ARRANGEMENT_EXEC_STATUS_RUNNING
)

class XiamiSeckillAppConfig(AppConfig):
    name = 'xiami_seckill_backend'

    def ready(self):
        self.logger = Logger().set_logger()
        is_django_startup = os.environ.get('DJANGO_START_UP') 
        if is_django_startup is None:
            os.environ['DJANGO_START_UP'] = 'True' 

            default_system_emailer_address = global_config.get('config', 'default_system_emailer_address')
            default_system_emailer_token = global_config.get('config', 'default_system_emailer_token')
            system_emailer = Emailer(None, default_system_emailer_address, default_system_emailer_token)

            self.execute_in_thread(self.query_arrangement_on_ready, [system_emailer])
            self.execute_in_thread(self.query_sys_info_on_ready, [system_emailer])
        else:
            self.logger.info('略过启动程序')
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

        self.logger.info('开始获取系统信息')

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

        self.logger.info('正在检查是否需要继续抢购')

        from .src.services.public.jd.jd_user_service import JDUserService
        from .src.services.public.common.login_user_service import LoginUserService
        from .src.services.public.jd.jd_seckill_service import JDSeckillService

        try:
            login_user_service = LoginUserService()
            jd_user_service = JDUserService()

            login_user_list = login_user_service.find_all_users()

            for user in login_user_list:
                login_username = user['username']
                self.logger.info('checking for user:' + login_username)
                jd_seckill_service = JDSeckillService(login_username)
                jd_user_arrangement_cache = jd_seckill_service.get_arrangement_status(login_username)
                db_arrangement = jd_user_service.find_jd_user_arrangement_by_username(login_username)

                self.logger.info('cache info')
                self.logger.info(jd_user_arrangement_cache)

                self.logger.info('db info')
                self.logger.info(db_arrangement)

                if not db_arrangement or 'seckill_arrangement' not in db_arrangement or len(str_to_json(db_arrangement['seckill_arrangement'])) == 0:
                    self.logger.info('no valid db arrangement, skip')
                    continue

                if not jd_user_arrangement_cache or len(jd_user_arrangement_cache) == 0:
                    self.logger.info('no valid cache arrangement, skip')
                    continue

                db_arrangement_json = str_to_json(db_arrangement['seckill_arrangement'])
                

                # [
                #     {
                #         "nick_name":"大大大大大大虾米",
                #         "leading_time":"90",
                #         "seckill_arangement":[
                #             {
                #                 "target_time":"2022-01-02 00:00:00.000",
                #                 "status":"planned"
                #             },
                #             {
                #                 "target_time":"2022-01-02 00:00:00.000",
                #                 "status":"planned"
                #             },
                #             {
                #                 "target_time":"2022-01-02 18:00:00.000",
                #                 "status":"planned"
                #             }
                #         ]
                #     }
                # ]

                if jd_user_arrangement_cache:
                    for login_user_arrangement in jd_user_arrangement_cache:
                        jd_username = login_user_arrangement['nick_name']
                        leading_time = login_user_arrangement['leading_time']
                        if 'seckill_arangement' not in login_user_arrangement or len(login_user_arrangement['seckill_arangement']) == 0:
                            self.logger.info('checking user:' + jd_username + ' has no cache arrangement, skip')
                            continue
                        arrangement_array = login_user_arrangement['seckill_arangement']
                        execution_arrangement_array = []
                        should_run_for_user = False
                        for item in arrangement_array:
                            execution_arrangement_item = {}
                            # check if expired
                            startTimeMills = get_timestamp_in_milli_sec(str_to_datetime(item['target_time']))
                            now_ts = get_timestamp_in_milli_sec(get_now_datetime())
                            if now_ts >= startTimeMills:
                                continue

                            status = item['status']
                            if status == ARRANGEMENT_EXEC_STATUS_RUNNING:
                                should_run_for_user = True

                            start_time_str = item['target_time']
                            sku_info = self._get_sku_from_db_arrangement(db_arrangement_json, jd_username, start_time_str)
                            if not sku_info or len(sku_info)==0:
                                continue
                            
                            sku_id = sku_info[0]['skuId']
                            num = sku_info[0]['count']

                            execution_arrangement_item['sku_id'] = sku_id
                            execution_arrangement_item['num'] = num
                            execution_arrangement_item['target_time'] = start_time_str
                            
                            execution_arrangement_array.append(execution_arrangement_item)

                        if should_run_for_user:
                            self.logger.info('正在恢复线程: ' + jd_username)
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
                            self.logger.info('用户:' + jd_username + '无需恢复线程')
        except Exception as e:
            system_emailer.send(subject='重启线程失败', content='重启线程失败')
            self.logger.error(traceback.format_exc())

    def _get_sku_from_db_arrangement(self, db_arrangement_json, jd_username, start_time_str):
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

        arrangement_user_array = db_arrangement_json[jd_username]

        for item in arrangement_user_array:
            startTimeItem = item['startTime']
            if startTimeItem == start_time_str:
                return item['skus']

        return None