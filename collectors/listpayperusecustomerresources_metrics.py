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
# 资源总数指标
RESOURCE_TOTAL_COUNT = Gauge(
    'huaweicloud_bss_resource_total_count',
    'Total count of pay-per-use resources in BSS',
    ['account']
)

# 资源状态指标 (1 for active, 0 for inactive)
RESOURCE_STATUS = Gauge(
    'huaweicloud_bss_resource_status',
    'Status of pay-per-use resources in BSS (1 for active, 0 for inactive)',
    ['account', 'region', 'resource_id', 'resource_name', 'service_type_name', 'resource_type_name']
)

# 资源规格大小指标
RESOURCE_SPEC_SIZE = Gauge(
    'huaweicloud_bss_resource_spec_size',
    'Specification size of pay-per-use resources in BSS',
    ['account', 'region', 'resource_id', 'resource_name', 'service_type_name', 'resource_type_name', 'spec_unit']
)

# 资源到期时间指标 (Unix时间戳)
RESOURCE_EXPIRE_TIME = Gauge(
    'huaweicloud_bss_resource_expire_timestamp',
    'Expire timestamp of pay-per-use resources in BSS (Unix timestamp)',
    ['account', 'region', 'resource_id', 'resource_name', 'service_type_name', 'resource_type_name']
)

# 资源生效时间指标 (Unix时间戳)
RESOURCE_EFFECTIVE_TIME = Gauge(
    'huaweicloud_bss_resource_effective_timestamp',
    'Effective timestamp of pay-per-use resources in BSS (Unix timestamp)',
    ['account', 'region', 'resource_id', 'resource_name', 'service_type_name', 'resource_type_name']
)

# 资源是否为主资源指标
RESOURCE_IS_MAIN = Gauge(
    'huaweicloud_bss_resource_is_main',
    'Whether the resource is main resource in BSS (1 for main, 0 for sub)',
    ['account', 'region', 'resource_id', 'resource_name', 'service_type_name', 'resource_type_name']
)

# 资源信息指标
RESOURCE_INFO = Info(
    'huaweicloud_bss_resource',
    'Detailed information of pay-per-use resources in BSS',
    ['account', 'region', 'resource_id', 'resource_name']
)


class LISTPAYPERUSECUSTOMERRESOURCESCollector(BaseCollector):
    """
    ListPayPerUseCustomerResources API指标收集器
    用于收集华为云账户中的包年/包月资源信息
    专门使用AK/SK认证方式和华为云SDK
    """
    
    def __init__(self, name, account_config, module_config=None):
        super().__init__(name, account_config, module_config)
        
        # 初始化华为云BSS客户端
        logger.debug(f"Initializing LISTPAYPERUSECUSTOMERRESOURCES collector for account {name}")
        try:
            # 使用配置中的AK/SK或者环境变量
            ak = self.ak or os.environ.get("CLOUD_SDK_AK")
            sk = self.sk or os.environ.get("CLOUD_SDK_SK")
            
            if not ak or not sk:
                logger.error(f"Missing AK/SK credentials for LISTPAYPERUSECUSTOMERRESOURCES collector in account {self.name}")
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
        收集ListPayPerUseCustomerResources API指标
        """
        logger.debug(f"Starting LISTPAYPERUSECUSTOMERRESOURCES metrics collection for account {self.name}")
        if not self.client:
            logger.warning(f"BSS client not initialized for LISTPAYPERUSECUSTOMERRESOURCES collector in account {self.name}")
            return
            
        try:
            # 构造请求参数
            request = ListPayPerUseCustomerResourcesRequest()
            logger.debug("ListPayPerUseCustomerResourcesRequest object created")
            
            # 根据配置文件中的参数构造请求体
            request_body = QueryResourcesReq()
            logger.debug("QueryResourcesReq object created")
            
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
            logger.debug("Calling list_pay_per_use_customer_resources API")
            response = self.client.list_pay_per_use_customer_resources(request)
            logger.debug("list_pay_per_use_customer_resources API call successful")
            
            # 解析响应数据
            data = response.to_json_object()
            logger.debug(f"Response data keys: {data.keys()}")
            
            # 更新资源总数指标
            total_count = data.get('total_count', 0)
            RESOURCE_TOTAL_COUNT.labels(account=self.name).set(total_count)
            logger.debug(f"Total pay-per-use resources count: {total_count}")
            
            # 解析资源列表数据并更新指标
            resource_list = data.get('data', [])
            logger.debug(f"Found {len(resource_list)} pay-per-use resources")
            
            # 如果没有资源，也要确保指标被设置
            if not resource_list:
                logger.info(f"No pay-per-use resources found for account {self.name}")
                return
            
            # 更新每个资源的详细指标
            for resource in resource_list:
                resource_id = resource.get('resource_id', 'unknown')
                resource_name = resource.get('resource_name', 'unknown')
                region = resource.get('region_code', 'unknown')
                service_type_name = resource.get('service_type_name', 'unknown')
                resource_type_name = resource.get('resource_type_name', 'unknown')
                
                logger.debug(f"Processing resource: {resource_id}, name: {resource_name}")
                
                # 资源状态指标 (将API状态码转换为0/1状态)
                # API状态码: 2：使用中 3：已关闭 4：已冻结 5：已过期
                status = resource.get('status', 0)
                # 确保status不是None
                if status is None:
                    status = 0
                status_value = 1 if status == 2 else 0  # 只有状态2(使用中)为1，其他为0
                RESOURCE_STATUS.labels(
                    account=self.name,
                    region=region,
                    resource_id=resource_id,
                    resource_name=resource_name,
                    service_type_name=service_type_name,
                    resource_type_name=resource_type_name
                ).set(status_value)
                logger.debug(f"Resource {resource_id} status: {status} -> {status_value}")
                
                # 资源规格大小指标
                spec_size = resource.get('spec_size', 0)
                # 确保spec_size不是None
                if spec_size is None:
                    spec_size = 0
                spec_unit_id = resource.get('spec_size_measure_id', 'unknown')
                # 确保spec_unit_id不是None
                if spec_unit_id is None:
                    spec_unit_id = 'unknown'
                # 将测量单位ID转换为可读单位
                spec_unit = self._get_spec_unit(spec_unit_id)
                RESOURCE_SPEC_SIZE.labels(
                    account=self.name,
                    region=region,
                    resource_id=resource_id,
                    resource_name=resource_name,
                    service_type_name=service_type_name,
                    resource_type_name=resource_type_name,
                    spec_unit=spec_unit
                ).set(spec_size)
                logger.debug(f"Resource {resource_id} spec size: {spec_size} {spec_unit}")
                
                # 资源信息指标
                resource_info = {
                    'id': resource.get('id', '') or '',
                    'service_type_name': resource.get('service_type_name', '') or '',
                    'resource_type_name': resource.get('resource_type_name', '') or '',
                    'product_spec_desc': resource.get('product_spec_desc', '') or '',
                    'project_id': resource.get('project_id', '') or '',
                    'parent_resource_id': resource.get('parent_resource_id', '') or '',
                    'enterprise_project_id': resource.get('enterprise_project', {}).get('id', '') or '' if resource.get('enterprise_project') is not None else '',
                    'enterprise_project_name': resource.get('enterprise_project', {}).get('name', '') or '' if resource.get('enterprise_project') is not None else ''
                }
                RESOURCE_INFO.labels(
                    account=self.name,
                    region=region,
                    resource_id=resource_id,
                    resource_name=resource_name
                ).info(resource_info)
                logger.debug(f"Resource {resource_id} info updated")
                
                # 资源到期时间指标 (转换为Unix时间戳)
                expire_time_str = resource.get('expire_time')
                if expire_time_str:
                    expire_timestamp = self._convert_to_timestamp(expire_time_str)
                    if expire_timestamp is not None:
                        RESOURCE_EXPIRE_TIME.labels(
                            account=self.name,
                            region=region,
                            resource_id=resource_id,
                            resource_name=resource_name,
                            service_type_name=service_type_name,
                            resource_type_name=resource_type_name
                        ).set(expire_timestamp)
                        logger.debug(f"Resource {resource_id} expire time: {expire_time_str} -> {expire_timestamp}")
                
                # 资源生效时间指标 (转换为Unix时间戳)
                effective_time_str = resource.get('effective_time')
                if effective_time_str:
                    effective_timestamp = self._convert_to_timestamp(effective_time_str)
                    if effective_timestamp is not None:
                        RESOURCE_EFFECTIVE_TIME.labels(
                            account=self.name,
                            region=region,
                            resource_id=resource_id,
                            resource_name=resource_name,
                            service_type_name=service_type_name,
                            resource_type_name=resource_type_name
                        ).set(effective_timestamp)
                        logger.debug(f"Resource {resource_id} effective time: {effective_time_str} -> {effective_timestamp}")
                
                # 资源是否为主资源指标
                is_main_resource = resource.get('is_main_resource', 0)
                # 确保is_main_resource不是None
                if is_main_resource is None:
                    is_main_resource = 0
                RESOURCE_IS_MAIN.labels(
                    account=self.name,
                    region=region,
                    resource_id=resource_id,
                    resource_name=resource_name,
                    service_type_name=service_type_name,
                    resource_type_name=resource_type_name
                ).set(is_main_resource)
                logger.debug(f"Resource {resource_id} is main resource: {is_main_resource}")
                
        except exceptions.ClientRequestException as e:
            logger.error(f"Error collecting LISTPAYPERUSECUSTOMERRESOURCES metrics for account {self.name}: "
                         f"status_code={e.status_code}, request_id={e.request_id}, "
                         f"error_code={e.error_code}, error_msg={e.error_msg}")
        except Exception as e:
            import traceback
            logger.error(f"Error collecting LISTPAYPERUSECUSTOMERRESOURCES metrics for account {self.name}: {e}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
        logger.debug(f"Completed LISTPAYPERUSECUSTOMERRESOURCES metrics collection for account {self.name}")
            
    def _get_spec_unit(self, measure_id):
        """
        根据测量单位ID获取单位名称
            
        :param measure_id: 测量单位ID
        :return: 单位名称
        """
        # 常见的测量单位映射
        unit_map = {
            15: 'Mbps',  # 典型的带宽单位
            17: 'GB',
            18: 'MB',
            19: 'TB',
            20: 'KB',
            # 可以根据需要添加更多单位
        }
        unit = unit_map.get(measure_id, f'unit_{measure_id}')
        logger.debug(f"Mapped spec measure_id {measure_id} to unit {unit}")
        return unit
            
    def _convert_to_timestamp(self, time_str):
        """
        将ISO时间字符串转换为Unix时间戳
            
        :param time_str: ISO时间字符串，如 "2024-10-10T07:45:56Z"
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
        logger.debug("Describing LISTPAYPERUSECUSTOMERRESOURCES collector metrics")
        return [
            RESOURCE_TOTAL_COUNT,
            RESOURCE_STATUS,
            RESOURCE_SPEC_SIZE,
            RESOURCE_INFO,
            RESOURCE_EXPIRE_TIME,
            RESOURCE_EFFECTIVE_TIME,
            RESOURCE_IS_MAIN
        ]