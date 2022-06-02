
# Response Body
DEFAULT_SUC_MESSAGE = "Operation Successful"
SUCCESS_CODE = 200

# login page
LOGIN_PAGE_URI = '/site/login'

# logging
LOG_FILENAME_PREFIX = 'jd-order'

# email 
SMTP_HOST = 'smtp.qq.com'
SMTP_PORT = 465

# HTTP Code
HTTP_CODE_200 = 200
HTTP_CODE_400 = 400
HTTP_CODE_401 = 401
HTTP_CODE_403 = 403
HTTP_CODE_500 = 500

# error category
PREFIX_REST = "REST"
ERROR_TYPE_COMMON = "1"
ERROR_TYPE_USER = "2"
ERROR_TYPE_SECKILL = "3"
ERROR_TYPE_ADMIN = "4"

USER_LEVEL_ADMIN = '1'
USER_LEVEL_NORMAL = '2'

JWT_HEADER_TOKEN_NAME = 'Authorization'
JWT_HEADER_USER_NAME = 'Logged-In-User'
JWT_HEADER_USER_LEVEL = 'Logged-In-User-Level'
JWT_HEADER_TOKEN_HEADER_NAME = 'Auth-Token'
JWT_AUTHZ_TYPE = 'Bearer'

# Default Timestamp Pattern
DATETIME_STR_PATTERN = "%Y-%m-%d %H:%M:%S.%f"
DATETIME_STR_PATTERN_SHORT = "%Y-%m-%d %H:%M:%S"

# Redis Cache

# 60 sec
DEFAULT_CACHE_TTL = 60
# 24 hour
DEFAULT_CACHE_STATUS_TTL = 86400
# 24 hour
DEFAULT_CACHE_SECKILL_INFO_TTL = 86400
# 60 sec
DEFAULT_QRCODE_TTL = 60
# 200 sec
DEFAULT_CACHE_MOBILE_CODE = 200

# cache key
SECKILL_INFO_CACHE_KEY = 'seckill_info_cache_key'
SYS_INFO_CACHE_KEY = 'sys_info_cache_key'

# lock key
LOCK_KEY_SECKILL_ARRANGEMENT = 'user_arrangement_lock_key'
LOCK_KEY_CANCEL_SECKILL_ARRANGEMENT = 'user_cencel_arrangement_lock_key'
LOCK_KEY_CUSTOM_SKU_DATA = 'user_custom_sku_data_lock_key'
LOCK_KEY_ADJUST_SERVER_TIME = 'adjust_server_time_lock_key'
LOCK_KEY_RANDOM_SKU_LIST = 'random_sku_list'
LOCK_KEY_RANDOM_SKU_STORE = 'random_sku_stock'

# JD constants
JD_PC_COOKIE_NAME = "jd-pc-cookies"
JD_MOBILE_COOKIE_NAME = "jd-mobile-cookies"

# RSA Key
RSA_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDC7kw8r6tq43pwApYvkJ5lalja
N9BZb21TAIfT/vexbobzH7Q8SUdP5uDPXEBKzOjx2L28y7Xs1d9v3tdPfKI2LR7P
AzWBmDMn8riHrDDNpUpJnlAGUqJG9ooPn8j7YNpcxCa1iybOlc2kEhmJn5uwoanQ
q+CA6agNkqly2H4j6wIDAQAB
-----END PUBLIC KEY-----"""

# Timeout
DEFAULT_TIMEOUT = 1

# User Agent
DEFAULT_MOBILE_USER_AGENT = 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Mobile Safari/537.36'
# DEFAULT_PC_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko'
DEFAULT_PC_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:64.0) Gecko/20100101 Firefox/64.'

# Execution status
ARRANGEMENT_EXEC_STATUS_PLANNED = 'planned'
ARRANGEMENT_EXEC_STATUS_RUNNING = 'running'
ARRANGEMENT_EXEC_STATUS_CANCELLED = 'cancelled'
ARRANGEMENT_EXEC_STATUS_SUCCEEDED = 'succeeded'
ARRANGEMENT_EXEC_STATUS_FAILED = 'failed'
ARRANGEMENT_EXEC_STATUS_ERROR = 'error'

# 随机商品过滤关键字
RANDOM_SKU_FILTER_OUT_LIST = ['胶水', '尺']