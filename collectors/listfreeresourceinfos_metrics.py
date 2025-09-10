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
# 免费资源包总数指标
TOTAL_COUNT = Gauge(
    'huaweicloud_bss_free_resource_package_total_count',
    'Total count of free resource packages in BSS',
    ['account']
)

# 免费资源包状态指标 (0:未生效, 1:生效中, 2:已用完, 3:已失效, 4:已退订)
PACKAGE_STATUS = Gauge(
    'huaweicloud_bss_free_resource_package_status',
    'Status of free resource packages in BSS (0:not effective, 1:in effect, 2:used up, 3:expired, 4:unsubscribed)',
    ['account', 'order_instance_id', 'product_name', 'service_type_name']
)

# 免费资源剩余额度指标
RESOURCE_AMOUNT = Gauge(
    'huaweicloud_bss_free_resource_amount',
    'Remaining amount of free resources in BSS',
    ['account', 'order_instance_id', 'product_name', 'usage_type_name', 'measure_unit']
)

# 免费资源原始额度指标
RESOURCE_ORIGINAL_AMOUNT = Gauge(
    'huaweicloud_bss_free_resource_original_amount',
    'Original amount of free resources in BSS',
    ['account', 'order_instance_id', 'product_name', 'usage_type_name', 'measure_unit']
)

# 免费资源包生效时间指标 (Unix时间戳)
PACKAGE_EFFECTIVE_TIME = Gauge(
    'huaweicloud_bss_free_resource_package_effective_timestamp',
    'Effective timestamp of free resource packages in BSS (Unix timestamp)',
    ['account', 'order_instance_id', 'product_name', 'service_type_name']
)

# 免费资源包到期时间指标 (Unix时间戳)
PACKAGE_EXPIRE_TIME = Gauge(
    'huaweicloud_bss_free_resource_package_expire_timestamp',
    'Expire timestamp of free resource packages in BSS (Unix timestamp)',
    ['account', 'order_instance_id', 'product_name', 'service_type_name']
)

# 正在使用中的免费资源包到期时间指标 (Unix时间戳)
ACTIVE_PACKAGE_EXPIRE_TIME = Gauge(
    'huaweicloud_bss_free_resource_active_package_expire_timestamp',
    'Expire timestamp of active free resource packages in BSS (Unix timestamp)',
    ['account', 'order_instance_id', 'product_name', 'service_type_name']
)

# 免费资源包信息指标
PACKAGE_INFO = Info(
    'huaweicloud_bss_free_resource_package',
    'Detailed information of free resource packages in BSS',
    ['account', 'order_instance_id', 'product_name']
)


class LISTFREERESOURCEINFOSCollector(BaseCollector):
    """
    ListFreeResourceInfos API指标收集器
    用于收集华为云账户中的免费资源包信息
    专门使用AK/SK认证方式和华为云SDK
    """
    
    def __init__(self, name, account_config, module_config=None):
        super().__init__(name, account_config, module_config)
        
        # 初始化华为云BSS客户端
        logger.debug(f"Initializing LISTFREERESOURCEINFOS collector for account {name}")
        try:
            # 使用配置中的AK/SK或者环境变量
            ak = self.ak or os.environ.get("CLOUD_SDK_AK")
            sk = self.sk or os.environ.get("CLOUD_SDK_SK")
            
            if not ak or not sk:
                logger.error(f"Missing AK/SK credentials for LISTFREERESOURCEINFOS collector in account {self.name}")
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
        收集ListFreeResourceInfos API指标
        """
        logger.debug(f"Starting LISTFREERESOURCEINFOS metrics collection for account {self.name}")
        if not self.client:
            logger.warning(f"BSS client not initialized for LISTFREERESOURCEINFOS collector in account {self.name}")
            return
            
        try:
            # 构造请求参数
            request = ListFreeResourceInfosRequest()
            logger.debug("ListFreeResourceInfosRequest object created")
            
            # 根据配置文件中的参数构造请求体
            request_body = ListFreeResourceInfosReq()
            logger.debug("ListFreeResourceInfosReq object created")
            
            if self.params:
                logger.debug(f"Applying parameters: {self.params}")
                # 添加配置文件中定义的参数
                for key, value in self.params.items():
                    if hasattr(request_body, key):
                        setattr(request_body, key, value)
                        logger.debug(f"Set {key} to {value}")
            
            request.body = request_body
            logger.debug("Request body assigned to request")
            
            # 调用华为云API
            logger.debug("Calling list_free_resource_infos API")
            response = self.client.list_free_resource_infos(request)
            logger.debug("list_free_resource_infos API call successful")
            
            # 解析响应数据
            data = response.to_json_object()
            logger.debug(f"Response data keys: {data.keys()}")
            
            # 更新免费资源包总数指标
            total_count = data.get('total_count', 0)
            TOTAL_COUNT.labels(account=self.name).set(total_count)
            logger.debug(f"Total free resource packages count: {total_count}")
            
            # 解析免费资源包列表数据并更新指标
            free_resource_packages = data.get('free_resource_packages', [])
            logger.debug(f"Found {len(free_resource_packages)} free resource packages")
            
            # 如果没有免费资源包，也要确保指标被设置
            if not free_resource_packages:
                logger.info(f"No free resource packages found for account {self.name}")
                return
            
            # 更新每个免费资源包的详细指标
            for package in free_resource_packages:
                order_instance_id = package.get('order_instance_id', 'unknown')
                product_name = package.get('product_name', 'unknown')
                service_type_name = package.get('service_type_name', 'unknown')
                
                logger.debug(f"Processing free resource package: {order_instance_id}, product: {product_name}")
                
                # 免费资源包状态指标
                status = package.get('status', 0)
                PACKAGE_STATUS.labels(
                    account=self.name,
                    order_instance_id=order_instance_id,
                    product_name=product_name,
                    service_type_name=service_type_name
                ).set(status)
                logger.debug(f"Package {order_instance_id} status: {status}")
                
                # 免费资源包信息指标
                package_info = {
                    'order_id': package.get('order_id', '') or '',
                    'product_id': package.get('product_id', '') or '',
                    'service_type_code': package.get('service_type_code', '') or '',
                    'region_code': package.get('region_code', '') or '',
                    'source_type': str(package.get('source_type', '')) or '',
                    'bundle_type': package.get('bundle_type', '') or '',
                    'quota_reuse_mode': str(package.get('quota_reuse_mode', '')) or ''
                }
                PACKAGE_INFO.labels(
                    account=self.name,
                    order_instance_id=order_instance_id,
                    product_name=product_name
                ).info(package_info)
                logger.debug(f"Package {order_instance_id} info updated")
                
                # 免费资源包生效时间指标 (转换为Unix时间戳)
                effective_time_str = package.get('effective_time')
                if effective_time_str:
                    effective_timestamp = self._convert_to_timestamp(effective_time_str)
                    if effective_timestamp is not None:
                        PACKAGE_EFFECTIVE_TIME.labels(
                            account=self.name,
                            order_instance_id=order_instance_id,
                            product_name=product_name,
                            service_type_name=service_type_name
                        ).set(effective_timestamp)
                        logger.debug(f"Package {order_instance_id} effective time: {effective_time_str} -> {effective_timestamp}")
                
                # 免费资源包到期时间指标 (转换为Unix时间戳)
                expire_time_str = package.get('expire_time')
                if expire_time_str:
                    expire_timestamp = self._convert_to_timestamp(expire_time_str)
                    if expire_timestamp is not None:
                        PACKAGE_EXPIRE_TIME.labels(
                            account=self.name,
                            order_instance_id=order_instance_id,
                            product_name=product_name,
                            service_type_name=service_type_name
                        ).set(expire_timestamp)
                        logger.debug(f"Package {order_instance_id} expire time: {expire_time_str} -> {expire_timestamp}")
                        
                        # 如果资源包状态为生效中(status=1)，则也更新正在使用中的资源包到期时间指标
                        if status == 1:
                            ACTIVE_PACKAGE_EXPIRE_TIME.labels(
                                account=self.name,
                                order_instance_id=order_instance_id,
                                product_name=product_name,
                                service_type_name=service_type_name
                            ).set(expire_timestamp)
                            logger.debug(f"Active package {order_instance_id} expire time: {expire_time_str} -> {expire_timestamp}")
                
                # 解析资源套餐内的资源项信息并更新指标
                free_resources = package.get('free_resources', [])
                logger.debug(f"Package {order_instance_id} contains {len(free_resources)} free resources")
                
                for resource in free_resources:
                    usage_type_name = resource.get('usage_type_name', 'unknown')
                    measure_id = resource.get('measure_id', 0)
                    # 将测量单位ID转换为可读单位
                    measure_unit = self._get_measure_unit(measure_id)
                    
                    logger.debug(f"Processing free resource: {usage_type_name}, measure_id: {measure_id}, unit: {measure_unit}")
                    
                    # 免费资源剩余额度指标
                    amount_str = resource.get('amount', '0')
                    try:
                        amount = float(amount_str)
                    except (ValueError, TypeError):
                        amount = 0.0
                    RESOURCE_AMOUNT.labels(
                        account=self.name,
                        order_instance_id=order_instance_id,
                        product_name=product_name,
                        usage_type_name=usage_type_name,
                        measure_unit=measure_unit
                    ).set(amount)
                    logger.debug(f"Resource {usage_type_name} amount: {amount}")
                    
                    # 免费资源原始额度指标
                    original_amount_str = resource.get('original_amount', '0')
                    try:
                        original_amount = float(original_amount_str)
                    except (ValueError, TypeError):
                        original_amount = 0.0
                    RESOURCE_ORIGINAL_AMOUNT.labels(
                        account=self.name,
                        order_instance_id=order_instance_id,
                        product_name=product_name,
                        usage_type_name=usage_type_name,
                        measure_unit=measure_unit
                    ).set(original_amount)
                    logger.debug(f"Resource {usage_type_name} original amount: {original_amount}")
                
        except exceptions.ClientRequestException as e:
            logger.error(f"Error collecting LISTFREERESOURCEINFOS metrics for account {self.name}: "
                         f"status_code={e.status_code}, request_id={e.request_id}, "
                         f"error_code={e.error_code}, error_msg={e.error_msg}")
        except Exception as e:
            import traceback
            logger.error(f"Error collecting LISTFREERESOURCEINFOS metrics for account {self.name}: {e}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
        logger.debug(f"Completed LISTFREERESOURCEINFOS metrics collection for account {self.name}")
            
    def _convert_to_timestamp(self, time_str):
        """
        将ISO时间字符串转换为Unix时间戳
            
        :param time_str: ISO时间字符串，如 "2024-09-10T01:09:42Z"
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
            
    def _get_measure_unit(self, measure_id):
        """
        根据测量单位ID获取单位名称
            
        :param measure_id: 测量单位ID
        :return: 单位名称
        """
        # 常见的测量单位映射
        unit_map = {
            10: 'GB',   # 典型的存储单位
            14: 'times', # 使用次数
            15: 'Mbps', # 带宽
            17: 'GB',   # 存储
            18: 'MB',   # 存储
            19: 'TB',   # 存储
            20: 'KB',   # 存储
            # 可以根据需要添加更多单位
        }
        unit = unit_map.get(measure_id, f'unit_{measure_id}')
        logger.debug(f"Mapped measure_id {measure_id} to unit {unit}")
        return unit
                
    def describe(self):
        """
        描述此收集器提供的指标
        """
        logger.debug("Describing LISTFREERESOURCEINFOS collector metrics")
        return [
            TOTAL_COUNT,
            PACKAGE_STATUS,
            RESOURCE_AMOUNT,
            RESOURCE_ORIGINAL_AMOUNT,
            PACKAGE_INFO,
            PACKAGE_EFFECTIVE_TIME,
            PACKAGE_EXPIRE_TIME,
            ACTIVE_PACKAGE_EXPIRE_TIME
        ]