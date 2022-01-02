from config.constants import (
    HTTP_CODE_200,
    HTTP_CODE_400,
    HTTP_CODE_401,
    HTTP_CODE_403,
    HTTP_CODE_500,
    PREFIX_REST,
    ERROR_TYPE_COMMON,
    ERROR_TYPE_USER,
    ERROR_TYPE_SECKILL
)

error_dict = {
    'COMMON':{
            'DEFAULT_ERROR':{
                'reasonCode': PREFIX_REST + ERROR_TYPE_COMMON + "000",
                'httpCode': HTTP_CODE_500,
                'msg': '无法预知错误'
            },
            'REQUEST_INVALID':{
                'reasonCode': PREFIX_REST + ERROR_TYPE_COMMON + "001",
                'httpCode': HTTP_CODE_400,
                'msg': '请求参数错误.'
            },
            'DATA_NOT_SYNC':{
                'reasonCode': PREFIX_REST + ERROR_TYPE_COMMON + "002",
                'httpCode': HTTP_CODE_400,
                'msg': '数据不同步.'
            },
            'UPDATE_ID_NOT_EXIST':{
                'reasonCode': PREFIX_REST + ERROR_TYPE_COMMON + "003",
                'httpCode': HTTP_CODE_403,
                'msg': '主键错误.'
            },
            'RESOURCE_NOT_ACCCESSABLE':{
                'reasonCode': PREFIX_REST + ERROR_TYPE_COMMON + "004",
                'httpCode': HTTP_CODE_403,
                'msg': '没有访问权限.'
            },
            'SECKILL_BATCH_LOAD_FAILURE':{
                'reasonCode': PREFIX_REST + ERROR_TYPE_COMMON + "005",
                'httpCode': HTTP_CODE_403,
                'msg': '获取秒杀信息失败.'
            },
            'API_LIMITED':{
                'reasonCode': PREFIX_REST + ERROR_TYPE_COMMON + "006",
                'httpCode': HTTP_CODE_403,
                'msg': 'API已被限流.'
            }
    },
    'USER':{
            'REQUEST_INVALID':{
                'reasonCode': PREFIX_REST + ERROR_TYPE_USER + "001",
                'httpCode': HTTP_CODE_401,
                'msg': '用户验证失败.'
            },
            'SESSION_TIMEOUT':{
                'reasonCode': PREFIX_REST + ERROR_TYPE_USER + "002",
                'httpCode': HTTP_CODE_401,
                'msg': 'Session过期.'
            },
            'TOKEN_INVALID':{
                'reasonCode': PREFIX_REST + ERROR_TYPE_USER + "003",
                'httpCode': HTTP_CODE_401,
                'msg': 'Token无效.'
            },
            'SC_KEY_BLANK':{
                'reasonCode': PREFIX_REST + ERROR_TYPE_USER + "004",
                'httpCode': HTTP_CODE_401,
                'msg': '微信推送key没有配置.'
            },
            'LOGIN_CRED_DUPLICATED':{
                'reasonCode': PREFIX_REST + ERROR_TYPE_USER + "005",
                'httpCode': HTTP_CODE_401,
                'msg': '用户登录信息冲突.'
            },
            'USER_DUPLICATED':{
                'reasonCode': PREFIX_REST + ERROR_TYPE_USER + "006",
                'httpCode': HTTP_CODE_401,
                'msg': '发现重复用户名.'
            },
            'PERMISSION_DENY':{
                'reasonCode': PREFIX_REST + ERROR_TYPE_USER + "007",
                'httpCode': HTTP_CODE_401,
                'msg': '用户无权限.'
            }
    },
    'ADMIN':{
            'USER_EXISTS':{
                'reasonCode': PREFIX_REST + ERROR_TYPE_USER + "001",
                'httpCode': HTTP_CODE_401,
                'msg': '用户名已存在.'
            }
    },
    'SERVICE':{
        'JD':{
            'QR_EXPIRED':{
                'reasonCode': PREFIX_REST + ERROR_TYPE_SECKILL + "001",
                'httpCode': HTTP_CODE_401,
                'msg': '二维码过期，请重新获取扫描'
            },
            'QR_INVALID':{
                'reasonCode': PREFIX_REST + ERROR_TYPE_SECKILL + "002",
                'httpCode': HTTP_CODE_401,
                'msg': '二维码信息校验失败'
            },
            'QR_DOWNLOAD_FAILURE':{
                'reasonCode': PREFIX_REST + ERROR_TYPE_SECKILL + "003",
                'httpCode': HTTP_CODE_401,
                'msg': '二维码下载失败'
            },
            'MOBILE_QR_ERROR':{
                'reasonCode': PREFIX_REST + ERROR_TYPE_SECKILL + "003",
                'httpCode': HTTP_CODE_401,
                'msg': 'QQ扫码失败'
            },
            'PC_NOT_LOGIN':{
                'reasonCode': PREFIX_REST + ERROR_TYPE_SECKILL + "005",
                'httpCode': HTTP_CODE_401,
                'msg': '电脑端非登录状态'
            },
            'MOBILE_LOGIN_FAILURE':{
                'reasonCode': PREFIX_REST + ERROR_TYPE_SECKILL + "006",
                'httpCode': HTTP_CODE_401,
                'msg': '移动端登录失败'
            },
            'STOCK_API_LIMITED':{
                'reasonCode': PREFIX_REST + ERROR_TYPE_SECKILL + "007",
                'httpCode': HTTP_CODE_403,
                'msg': '公共库存查询接口已被限流'
            },
            'USER_MOBILE_COOKIE_FAILURE':{
                'reasonCode': PREFIX_REST + ERROR_TYPE_SECKILL + "008",
                'httpCode': HTTP_CODE_401,
                'msg': '测试移动端cookie有效性失败'
            },
            'GET_BATCH_SECKILL_FAILURE':{
                'reasonCode': PREFIX_REST + ERROR_TYPE_SECKILL + "009",
                'httpCode': HTTP_CODE_500,
                'msg': '获取秒杀信息失败'
            },
            'INIT_SECKILL_FAILURE':{
                'reasonCode': PREFIX_REST + ERROR_TYPE_SECKILL + "010",
                'httpCode': HTTP_CODE_500,
                'msg': '初始化秒杀失败'
            },
            'MANUAL_RESERVE_REQUIRED':{
                'reasonCode': PREFIX_REST + ERROR_TYPE_SECKILL + "011",
                'httpCode': HTTP_CODE_500,
                'msg': '商品需要手动预约'
            },
            'MOBILE_QR_UPDATED':{
                'reasonCode': PREFIX_REST + ERROR_TYPE_SECKILL + "012",
                'httpCode': HTTP_CODE_401,
                'msg': 'QQ扫码失败, 点击关联QQ按钮重新关联'
            },
            'MOBILE_QQ_BINDING':{
                'reasonCode': PREFIX_REST + ERROR_TYPE_SECKILL + "012",
                'httpCode': HTTP_CODE_401,
                'msg': 'QQ账号没有绑定京东，点击关联QQ按钮绑定京东账号'
            },
            'ADDR_NO_STOCK':{
                'reasonCode': PREFIX_REST + ERROR_TYPE_SECKILL + "013",
                'httpCode': HTTP_CODE_500,
                'msg': '抱歉，您当前选择的城市无法购买商品'
            },
        }
    }
}

