
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
LOCK_KEY_H5ST = 'lock_key_h5st'
LOCK_KEY_TRACEID = 'lock_key_traceid'
LOCK_KEY_MARATHON_CREATE_ORDER = 'lock_key_marathon_create_order'

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
DEFAULT_MOBILE_USER_AGENT = 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1'
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

# 服务器 ip 地址段
SERVER_IP_PREFIX = '39.103'

# 随机mobile user agent
MOBILE_UA_LIST = [
'Mozilla/5.0 (Linux; U; Android 4.0.3; ko-kr; LG-L160L Build/IML74K) AppleWebkit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30',
'Mozilla/5.0 (Linux; U; Android 4.0.3; de-ch; HTC Sensation Build/IML74K) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30',
'Mozilla/5.0 (Linux; U; Android 2.3; en-us) AppleWebKit/999+ (KHTML, like Gecko) Safari/999.9',
'Mozilla/5.0 (Linux; U; Android 2.3.5; zh-cn; HTC_IncredibleS_S710e Build/GRJ90) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1',
'Mozilla/5.0 (Linux; U; Android 2.3.5; en-us; HTC Vision Build/GRI40) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1',
'Mozilla/5.0 (Linux; U; Android 2.3.4; fr-fr; HTC Desire Build/GRJ22) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1',
'Mozilla/5.0 (Linux; U; Android 2.3.4; en-us; T-Mobile myTouch 3G Slide Build/GRI40) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1',
'Mozilla/5.0 (Linux; U; Android 2.3.3; zh-tw; HTC_Pyramid Build/GRI40) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1',
'Mozilla/5.0 (Linux; U; Android 2.3.3; zh-tw; HTC_Pyramid Build/GRI40) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari',
'Mozilla/5.0 (Linux; U; Android 2.3.3; zh-tw; HTC Pyramid Build/GRI40) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1',
'Mozilla/5.0 (Linux; U; Android 2.3.3; ko-kr; LG-LU3000 Build/GRI40) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1',
'Mozilla/5.0 (Linux; U; Android 2.3.3; en-us; HTC_DesireS_S510e Build/GRI40) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1',
'Mozilla/5.0 (Linux; U; Android 2.3.3; en-us; HTC_DesireS_S510e Build/GRI40) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile',
'Mozilla/5.0 (Linux; U; Android 2.3.3; de-de; HTC Desire Build/GRI40) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1',
'Mozilla/5.0 (Linux; U; Android 2.3.3; de-ch; HTC Desire Build/FRF91) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1',
'Mozilla/5.0 (Linux; U; Android 2.2; fr-lu; HTC Legend Build/FRF91) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1',
'Mozilla/5.0 (Linux; U; Android 2.2; en-sa; HTC_DesireHD_A9191 Build/FRF91) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1',
'Mozilla/5.0 (Linux; U; Android 2.2.1; fr-fr; HTC_DesireZ_A7272 Build/FRG83D) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1',
'Mozilla/5.0 (Linux; U; Android 2.2.1; en-gb; HTC_DesireZ_A7272 Build/FRG83D) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1',
'Mozilla/5.0 (Linux; U; Android 2.2.1; en-ca; LG-P505R Build/FRG83) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1',
'Mozilla/5.0 (Windows; U; Windows CE; Mobile; like Android; ko-kr) AppleWebKit/533.3 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.3 Dorothy',
'Mozilla/5.0 (Android; Linux armv7l; rv:9.0) Gecko/20111216 Firefox/9.0 Fennec/9.0',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; fr; rv:1.9.2.18) Gecko/20110614 Mozilla/5.0 (Android; Linux armv7l; rv:5.0) Gecko/20110615 Firefox/5.0 Fennec/5.0',
'Mozilla/5.0 (Android; WOW64; Linux armv7l;rv:5.0) Gecko/20110603 Firefox/5.0 Fennec/5.0',
'Mozilla/5.0 (Android; Linux armv7l;rv:5.0) Gecko/20110603 Firefox/5.0 Fennec/5.0',
'Mozilla/5.0 (Android; Linux armv7l; rv:5.0) Gecko/20110615 Firefox/5.0 Fennec/5.0',
'Mozilla/5.0 (Android; Linux armv7l; rv:5.0) Gecko/20110614 Firefox/5.0 Fennec/5.0',
'Mozilla/5.0 (Android; Linux armv7l; rv:5.0) Gecko/20110517 Firefox/5.0 Fennec/5.0',
'Mozilla/5.0 (Android; Linux armv71; rv:5.0) Gecko/20110615 Fennec/5.0',
'Mozilla/5.0 (Android; Linux armv7l; rv:2.2a1pre) Gecko/20110403 Firefox/4.2a1pre Fennec/4.1a1pre',
'Mozilla/5.0 (Android; Linux armv7l; rv:2.2a1pre) Gecko/20110402 Firefox/4.2a1pre Fennec/4.1a1pre',
'Mozilla/5.0 (Android; Linux armv7l; rv:2.0b9pre) Gecko/20110103 Firefox/4.0b9pre Fennec/4.0b4pre',
'Mozilla/5.0 (Linux; U; Android 2.2; en-us; T-Mobile HTC_G2 Build/FRF91) Gecko/20110415 Firefox/4.0.2pre Fennec/4.0.1',
'Mozilla/5.0 (Android; Linux armv7l; rv:2.1.1) Gecko/20110415 Firefox/4.0.2pre Fennec/4.0.1',
'Mozilla/5.0 (Android; Linux armv7l; rv:2.1.1) Gecko/20110415 Fennec/4.0.1',
'Mozilla/5.0 (Android; Linux arm7l; rv:2.1.1) Gecko/20110415 Firefox/4.0.2pre Fennec/4.0.1',
'Mozilla/5.0 (Android; Linux arm71; rv:2.1.1) Gecko/20110415 Firefox/4.0.2pre Fennec/4.0.1',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; fr; rv:1.9.2.13) Gecko/20101203 Mozilla/5.O(Android;Linux armv7l;rv:2.1) Gecko/20110318 Firefox/4.0b13pre Fennec/4.0 ( .NET CLR 3.5.30729)',
'Mozilla/5.0 (Android; Linux armv7l; rv:2.1) Gecko/20110318 Firefox/4.0b13pre Fennec/4.0',
'Mozilla/5.0 (Android; Linux armv7l; rv:2.0) Gecko/20110103 Firefox/4.0 Fennec/4.0',
'Mozilla/5.0 (Android; Linux armv71; rv:2.1) Gecko/20110318 Firefox/4.0b13pre Fennec/4.0',
'Mozilla/5.0 (Android) Gecko/20110318 Firefox/4.0 Fennec/4.0',
'Mozilla/5.0 (Android) Gecko Firefox Fennec/4.0',
'Mozilla/5.0 (Android; Linux armv7l; rv:2.0.1) Gecko/20100101 Fennec/2.0.1',
'Mozilla/5.0 (Android 2.2; zh-cn; HTC Desire)/GoBrowser',
'Opera/9.80 (Android; Opera Mini/7.5.33361/31.1350; U; en) Presto/2.8.119 Version/11.10',
'Opera/9.80 (Android; Opera Mini/7.29530/27.1407; U; en) Presto/2.8.119 Version/11.10',
'Opera/9.80 (Android; Opera Mini/7.0.29952/28.2075; U; es) Presto/2.8.119 Version/11.10',
'Opera/9.80 (Android; Opera Mini/6.1.25375/25.657; U; es) Presto/2.5.25 Version/10.54',
'Opera/9.80 (Android;Opera Mini/6.0.24212/24.746 U;en) Presto/2.5.25 Version/10.5454',
'Opera/9.80 (Android; Opera Mini/5.1.22460/23.334; U; en) Presto/2.5.25 Version/10.54',
'Opera/9.80 (Android; Opera Mini/5.1.22460/22.478; U; fr) Presto/2.5.25 Version/10.54',
'Opera/9.80 (Android; Opera Mini/5.1.22460/22.414; U; de) Presto/2.5.25 Version/10.54',
'Opera/9.80 (Android; Opera Mini/5.1.21126/19.892; U; de) Presto/2.5.25',
'Opera/9.80 (J2ME/MIDP; Opera Mini/5.0 (Linux; U; Android 2.2; fr-lu; HTC Legend Build/24.838; U; en) Presto/2.5.25 Version/10.54',
'Opera/9.80 (J2ME/MIDP; Opera Mini/5.0 (Linux; U; Android 2.2; en-sa; HTC_DesireHD_A9191 Build/24.741; U; en) Presto/2.5.25 Version/10.54',
'Opera/12.02 (Android 4.1; Linux; Opera Mobi/ADR-1111101157; U; en-US) Presto/2.9.201 Version/12.02',
'Opera/9.80 (Android 2.3.3; Linux; Opera Mobi/ADR-1111101157; U; es-ES) Presto/2.9.201 Version/11.50',
'Opera/9.80 (Android 2.3.4; Linux; Opera Mobi/build-1107180945; U; en-GB) Presto/2.8.149 Version/11.10',
'Opera/9.80 (Android 2.2.1; Linux; Opera Mobi/ADR-1107051709; U; pl) Presto/2.8.149 Version/11.10',
'Opera/9.80 (Android; Linux; Opera Mobi/ADR-1012221546; U; pl) Presto/2.7.60 Version/10.5',
'Opera/9.80 (Android 2.2;;; Linux; Opera Mobi/ADR-1012291359; U; en) Presto/2.7.60 Version/10.5',
'Opera/9.80 (Android 2.2; Opera Mobi/ADR-2093533608; U; pl) Presto/2.7.60 Version/10.5',
'Opera/9.80 (Android 2.2; Opera Mobi/-2118645896; U; pl) Presto/2.7.60 Version/10.5',
'Opera/9.80 (Android 2.2; Linux; Opera Mobi/ADR-2093533312; U; pl) Presto/2.7.60 Version/10.5',
'Opera/9.80 (Android 2.2; Linux; Opera Mobi/ADR-2093533120; U; pl) Presto/2.7.60 Version/10.5',
'Opera/9.80 (Android 2.2; Linux; Opera Mobi/8745; U; en) Presto/2.7.60 Version/10.5',
'Opera/9.80 (Android; Linux; Opera Mobi/ADR-1012211514; U; en) Presto/2.6.35 Version/10.1',
'Opera/9.80 (Android; Linux; Opera Mobi/ADR-1011151731; U; de) Presto/2.5.28 Version/10.1',
'Opera/9.80 (Android; Linux; Opera Mobi/ADR-1012272315; U; pl) Presto/2.7.60 Version/10.5',
'Opera/9.80 (Android; Linux; Opera Mobi/49; U; en) Presto/2.4.18 Version/10.00',
'Opera/9.80 (Android; Linux; Opera Mobi/27; U; en) Presto/2.4.18 Version/10.00',
'Mozilla/5.0 (Android 2.2.2; Linux; Opera Mobi/ADR-1103311355; U; en; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6 Opera 11.00',
'Mozilla/4.0 (compatible; MSIE 8.0; Android 2.2.2; Linux; Opera Mobi/ADR-1103311355; en) Opera 11.00'
]