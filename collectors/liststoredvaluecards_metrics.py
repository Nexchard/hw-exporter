from collectors.base_collector import BaseCollector
from prometheus_client import Gauge, Info
import logging
import os

# 导入华为云SDK相关模块
from huaweicloudsdkcore.auth.credentials import GlobalCredentials
from huaweicloudsdkbss.v2.region.bss_region import BssRegion
from huaweicloudsdkcore.exceptions import exceptions
from huaweicloudsdkbss.v2 import *

logger = logging.getLogger(__name__)

# 定义模块级指标，避免重复注册
# 储值卡总数指标
TOTAL_COUNT = Gauge(
    'huaweicloud_bss_stored_value_card_total_count',
    'Total count of stored value cards in BSS',
    ['account']
)

# 储值卡状态指标 (1 for available, 2 for used up)
CARD_STATUS = Gauge(
    'huaweicloud_bss_stored_value_card_status',
    'Status of stored value cards in BSS (1 for available, 2 for used up)',
    ['account', 'card_id', 'card_name']
)

# 储值卡面值指标
CARD_FACE_VALUE = Gauge(
    'huaweicloud_bss_stored_value_card_face_value',
    'Face value of stored value cards in BSS',
    ['account', 'card_id', 'card_name', 'currency']
)

# 储值卡余额指标
CARD_BALANCE = Gauge(
    'huaweicloud_bss_stored_value_card_balance',
    'Balance of stored value cards in BSS',
    ['account', 'card_id', 'card_name', 'currency']
)

# 储值卡生效时间指标 (Unix时间戳)
CARD_EFFECTIVE_TIME = Gauge(
    'huaweicloud_bss_stored_value_card_effective_timestamp',
    'Effective timestamp of stored value cards in BSS (Unix timestamp)',
    ['account', 'card_id', 'card_name']
)

# 储值卡到期时间指标 (Unix时间戳)
CARD_EXPIRE_TIME = Gauge(
    'huaweicloud_bss_stored_value_card_expire_timestamp',
    'Expire timestamp of stored value cards in BSS (Unix timestamp)',
    ['account', 'card_id', 'card_name']
)

# 储值卡信息指标
CARD_INFO = Info(
    'huaweicloud_bss_stored_value_card',
    'Detailed information of stored value cards in BSS',
    ['account', 'card_id', 'card_name']
)


class LISTSTOREDVALUECARDSCollector(BaseCollector):
    """
    ListStoredValueCards API指标收集器
    用于收集华为云账户中的储值卡信息
    专门使用AK/SK认证方式和华为云SDK
    """
    
    def __init__(self, name, account_config, module_config=None):
        super().__init__(name, account_config, module_config)
        
        # 初始化华为云BSS客户端
        logger.debug(f"Initializing LISTSTOREDVALUECARDS collector for account {name}")
        try:
            # 使用配置中的AK/SK或者环境变量
            ak = self.ak or os.environ.get("CLOUD_SDK_AK")
            sk = self.sk or os.environ.get("CLOUD_SDK_SK")
            
            if not ak or not sk:
                logger.error(f"Missing AK/SK credentials for LISTSTOREDVALUECARDS collector in account {self.name}")
                self.client = None
                return
                
            credentials = GlobalCredentials(ak, sk)
            logger.debug("GlobalCredentials created successfully")
            
            # 使用配置中的区域或者默认区域
            region = self.region or "cn-north-1"
            logger.debug(f"Using region: {region}")
            
            self.client = BssClient.new_builder() \
                .with_credentials(credentials) \
                .with_region(BssRegion.value_of(region)) \
                .build()
            logger.debug("BSS client initialized successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize BSS client for account {self.name}: {e}")
            self.client = None

    def collect(self):
        """
        收集ListStoredValueCards API指标
        """
        logger.debug(f"Starting LISTSTOREDVALUECARDS metrics collection for account {self.name}")
        if not self.client:
            logger.warning(f"BSS client not initialized for LISTSTOREDVALUECARDS collector in account {self.name}")
            return
            
        try:
            # 构造请求参数
            request = ListStoredValueCardsRequest()
            logger.debug("ListStoredValueCardsRequest object created")
            
            # 根据配置文件中的参数构造请求参数
            if self.params:
                logger.debug(f"Applying parameters: {self.params}")
                # 添加配置文件中定义的参数
                for key, value in self.params.items():
                    if hasattr(request, key):
                        setattr(request, key, value)
                        logger.debug(f"Set {key} to {value}")
            
            # 调用华为云API
            logger.debug("Calling list_stored_value_cards API")
            response = self.client.list_stored_value_cards(request)
            logger.debug("list_stored_value_cards API call successful")
            
            # 解析响应数据
            data = response.to_json_object()
            logger.debug(f"Response data keys: {data.keys()}")
            
            # 更新储值卡总数指标
            total_count = data.get('total_count', 0)
            TOTAL_COUNT.labels(account=self.name).set(total_count)
            logger.debug(f"Total stored value cards count: {total_count}")
            
            # 解析储值卡列表数据并更新指标
            stored_value_cards = data.get('stored_value_cards', [])
            logger.debug(f"Found {len(stored_value_cards)} stored value cards")
            
            # 如果没有储值卡，也要确保指标被设置
            if not stored_value_cards:
                logger.info(f"No stored value cards found for account {self.name}")
                return
            
            # 更新每个储值卡的详细指标
            for card in stored_value_cards:
                card_id = card.get('card_id', 'unknown')
                card_name = card.get('card_name', 'unknown')
                
                logger.debug(f"Processing stored value card: {card_id}, name: {card_name}")
                
                # 储值卡状态指标
                status = card.get('status', 0)
                CARD_STATUS.labels(
                    account=self.name,
                    card_id=card_id,
                    card_name=card_name
                ).set(status)
                logger.debug(f"Card {card_id} status: {status}")
                
                # 储值卡面值指标 (转换为浮点数)
                face_value_str = card.get('face_value', '0')
                try:
                    face_value = float(face_value_str)
                except (ValueError, TypeError):
                    face_value = 0.0
                CARD_FACE_VALUE.labels(
                    account=self.name,
                    card_id=card_id,
                    card_name=card_name,
                    currency='CNY'  # 默认人民币
                ).set(face_value)
                logger.debug(f"Card {card_id} face value: {face_value}")
                
                # 储值卡余额指标 (转换为浮点数)
                balance_str = card.get('balance', '0')
                try:
                    balance = float(balance_str)
                except (ValueError, TypeError):
                    balance = 0.0
                CARD_BALANCE.labels(
                    account=self.name,
                    card_id=card_id,
                    card_name=card_name,
                    currency='CNY'  # 默认人民币
                ).set(balance)
                logger.debug(f"Card {card_id} balance: {balance}")
                
                # 储值卡信息指标
                card_info = {
                    'status': str(card.get('status', '')) or '',
                    'face_value': card.get('face_value', '') or '',
                    'balance': card.get('balance', '') or '',
                    'effective_time': card.get('effective_time', '') or '',
                    'expire_time': card.get('expire_time', '') or ''
                }
                CARD_INFO.labels(
                    account=self.name,
                    card_id=card_id,
                    card_name=card_name
                ).info(card_info)
                logger.debug(f"Card {card_id} info updated")
                
                # 储值卡生效时间指标 (转换为Unix时间戳)
                effective_time_str = card.get('effective_time')
                if effective_time_str:
                    effective_timestamp = self._convert_to_timestamp(effective_time_str)
                    if effective_timestamp is not None:
                        CARD_EFFECTIVE_TIME.labels(
                            account=self.name,
                            card_id=card_id,
                            card_name=card_name
                        ).set(effective_timestamp)
                        logger.debug(f"Card {card_id} effective time: {effective_time_str} -> {effective_timestamp}")
                
                # 储值卡到期时间指标 (转换为Unix时间戳)
                expire_time_str = card.get('expire_time')
                if expire_time_str:
                    expire_timestamp = self._convert_to_timestamp(expire_time_str)
                    if expire_timestamp is not None:
                        CARD_EXPIRE_TIME.labels(
                            account=self.name,
                            card_id=card_id,
                            card_name=card_name
                        ).set(expire_timestamp)
                        logger.debug(f"Card {card_id} expire time: {expire_time_str} -> {expire_timestamp}")
                
        except exceptions.ClientRequestException as e:
            logger.error(f"Error collecting LISTSTOREDVALUECARDS metrics for account {self.name}: "
                         f"status_code={e.status_code}, request_id={e.request_id}, "
                         f"error_code={e.error_code}, error_msg={e.error_msg}")
        except Exception as e:
            import traceback
            logger.error(f"Error collecting LISTSTOREDVALUECARDS metrics for account {self.name}: {e}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
        logger.debug(f"Completed LISTSTOREDVALUECARDS metrics collection for account {self.name}")
            
    def _convert_to_timestamp(self, time_str):
        """
        将ISO时间字符串转换为Unix时间戳
            
        :param time_str: ISO时间字符串，如 "2022-11-29T06:48:45Z"
        :return: Unix时间戳
        """
        import datetime
        try:
            # 解析ISO时间字符串
            dt = datetime.datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%SZ")
            # 转换为Unix时间戳
            timestamp = dt.timestamp()
            logger.debug(f"Converted time string {time_str} to timestamp {timestamp}")
            return timestamp
        except Exception as e:
            logger.warning(f"Failed to convert time string {time_str} to timestamp: {e}")
            return None
                
    def describe(self):
        """
        描述此收集器提供的指标
        """
        logger.debug("Describing LISTSTOREDVALUECARDS collector metrics")
        return [
            TOTAL_COUNT,
            CARD_STATUS,
            CARD_FACE_VALUE,
            CARD_BALANCE,
            CARD_INFO,
            CARD_EFFECTIVE_TIME,
            CARD_EXPIRE_TIME
        ]