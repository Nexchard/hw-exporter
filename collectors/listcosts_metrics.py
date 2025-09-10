from collectors.base_collector import BaseCollector
from prometheus_client import Gauge, Info
import logging
import os
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# 导入华为云SDK相关模块
from huaweicloudsdkcore.auth.credentials import GlobalCredentials
from huaweicloudsdkbss.v2.region.bss_region import BssRegion
from huaweicloudsdkcore.exceptions import exceptions
from huaweicloudsdkbss.v2 import *

logger = logging.getLogger(__name__)

# 定义模块级指标，避免重复注册
# 成本金额指标
COST_AMOUNT = Gauge(
    'huaweicloud_bss_cost_amount',
    'Cost amount in BSS',
    ['account', 'dimension_key', 'dimension_value', 'time_dimension_value', 'amount_type']
)

# 官方成本金额指标
OFFICIAL_COST_AMOUNT = Gauge(
    'huaweicloud_bss_official_cost_amount',
    'Official cost amount in BSS',
    ['account', 'dimension_key', 'dimension_value', 'time_dimension_value']
)

# 成本汇总信息指标
COST_SUMMARY = Gauge(
    'huaweicloud_bss_cost_summary',
    'Cost summary by dimension in BSS',
    ['account', 'dimension_key', 'dimension_value', 'summary_type']
)


class LISTCOSTSCollector(BaseCollector):
    """
    ListCosts API指标收集器
    用于收集华为云账户中的成本信息
    专门使用AK/SK认证方式和华为云SDK
    """

    def __init__(self, name, account_config, module_config=None):
        super().__init__(name, account_config, module_config)
        
        # 初始化华为云BSS客户端
        logger.debug(f"Initializing LISTCOSTS collector for account {name}")
        try:
            # 使用配置中的AK/SK或者环境变量
            ak = self.ak or os.environ.get("CLOUD_SDK_AK")
            sk = self.sk or os.environ.get("CLOUD_SDK_SK")
            
            if not ak or not sk:
                logger.error(f"Missing AK/SK credentials for LISTCosts collector in account {self.name}")
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
        收集ListCosts API指标
        """
        logger.debug(f"Starting LISTCOSTS metrics collection for account {self.name}")
        if not self.client:
            logger.warning(f"BSS client not initialized for LISTCosts collector in account {self.name}")
            return
            
        try:
            # 构造请求参数
            request = ListCostsRequest()
            logger.debug("ListCostsRequest object created")
            
            # 自动生成时间范围：基于当前月份的上一个月往前推12个月
            # 例如今天是2025年9月4日，应该查询2024年8月至2025年8月的数据
            current_date = datetime.now()
            # 获取上一个月作为结束时间
            end_date = current_date - relativedelta(months=1)
            # 格式化为YYYY-MM
            end_time = end_date.strftime("%Y-%m")
            # 计算开始时间：往前推12个月
            start_date = end_date - relativedelta(months=11)
            begin_time = start_date.strftime("%Y-%m")
            
            logger.debug(f"Auto-generated time range: {begin_time} to {end_time}")
            
            # 如果配置中有参数，则使用配置中的参数
            if self.params:
                logger.debug(f"Applying parameters: {self.params}")
                if 'begin_time' in self.params:
                    begin_time = self.params['begin_time']
                    logger.debug(f"Overriding begin_time with config value: {begin_time}")
                if 'end_time' in self.params:
                    end_time = self.params['end_time']
                    logger.debug(f"Overriding end_time with config value: {end_time}")
            
            # 构造时间条件
            time_condition = TimeCondition(
                time_measure_id=2,  # 月粒度
                begin_time=begin_time,
                end_time=end_time
            )
            logger.debug(f"TimeCondition created: time_measure_id=2, begin_time={begin_time}, end_time={end_time}")
            
            # 构造分组条件 - 默认按计费模式分组
            groupby_list = [
                GroupBy(
                    type="dimension",
                    key="CHARGING_MODE"
                )
            ]
            logger.debug("Default groupby condition created: CHARGING_MODE")
            
            # 构造请求体
            request_body = ListCostsReq(
                amount_type="NET_AMOUNT",     # 默认净额
                cost_type="ORIGINAL_COST",    # 默认原始成本
                groupby=groupby_list,
                time_condition=time_condition,
                filters=[]  # 默认无过滤条件
            )
            logger.debug("ListCostsReq created with default values")
            
            # 如果配置中有参数，则使用配置中的参数覆盖默认值
            if self.params:
                if 'amount_type' in self.params:
                    request_body.amount_type = self.params['amount_type']
                    logger.debug(f"Overriding amount_type with config value: {request_body.amount_type}")
                if 'cost_type' in self.params:
                    request_body.cost_type = self.params['cost_type']
                    logger.debug(f"Overriding cost_type with config value: {request_body.cost_type}")
                if 'groupby' in self.params:
                    # 需要将配置中的groupby参数转换为SDK对象
                    groupby_list = []
                    for groupby_item in self.params['groupby']:
                        groupby_obj = GroupBy(
                            type=groupby_item.get('type', 'dimension'),
                            key=groupby_item.get('key')
                        )
                        groupby_list.append(groupby_obj)
                        logger.debug(f"Added groupby condition: type={groupby_obj.type}, key={groupby_obj.key}")
                    request_body.groupby = groupby_list
                if 'filters' in self.params:
                    request_body.filters = self.params['filters']
                    logger.debug(f"Overriding filters with config value: {request_body.filters}")
            
            request.body = request_body
            logger.debug("Request body assigned to request")
            
            # 调用华为云API
            logger.debug("Calling list_costs API")
            response = self.client.list_costs(request)
            logger.debug("list_costs API call successful")
            
            # 解析响应数据
            data = response.to_json_object()
            logger.debug(f"Response data keys: {data.keys()}")
            
            # 获取货币单位
            currency = data.get('currency', 'CNY')
            logger.debug(f"Currency: {currency}")
            
            # 解析成本数据并更新指标
            cost_data = data.get('cost_data', [])
            logger.debug(f"Found {len(cost_data)} cost data items")
            
            # 如果没有成本数据，也要确保指标被设置
            if not cost_data:
                logger.info(f"No cost data found for account {self.name}")
                return
            
            # 更新每个成本数据的详细指标
            for cost_item in cost_data:
                dimensions = cost_item.get('dimensions', [])
                dimension_key = 'unknown'
                dimension_value = 'unknown'
                
                # 获取维度信息
                if dimensions:
                    dimension = dimensions[0]
                    dimension_key = dimension.get('key', 'unknown')
                    dimension_value = dimension.get('value', 'unknown')
                
                logger.debug(f"Processing cost item with dimension: {dimension_key} = {dimension_value}")
                
                # 获取成本详情
                costs = cost_item.get('costs', [])
                logger.debug(f"Found {len(costs)} cost entries for this dimension")
                
                # 更新每个时间点的成本指标
                for cost in costs:
                    time_dimension_value = cost.get('time_dimension_value', 'unknown')
                    amount = float(cost.get('amount', 0))
                    official_amount = float(cost.get('official_amount', 0))
                    
                    logger.debug(f"Processing cost for time {time_dimension_value}: amount={amount}, official_amount={official_amount}")
                    
                    # 更新成本金额指标
                    COST_AMOUNT.labels(
                        account=self.name,
                        dimension_key=dimension_key,
                        dimension_value=dimension_value,
                        time_dimension_value=time_dimension_value,
                        amount_type='net_amount'
                    ).set(amount)
                    
                    # 更新官方成本金额指标
                    OFFICIAL_COST_AMOUNT.labels(
                        account=self.name,
                        dimension_key=dimension_key,
                        dimension_value=dimension_value,
                        time_dimension_value=time_dimension_value
                    ).set(official_amount)
                
                # 更新成本汇总信息
                amount_by_costs = float(cost_item.get('amount_by_costs', 0))
                official_amount_by_costs = float(cost_item.get('official_amount_by_costs', 0))
                
                logger.debug(f"Cost summary: amount_by_costs={amount_by_costs}, official_amount_by_costs={official_amount_by_costs}")
                
                COST_SUMMARY.labels(
                    account=self.name,
                    dimension_key=dimension_key,
                    dimension_value=dimension_value,
                    summary_type='net_amount'
                ).set(amount_by_costs)
                
                COST_SUMMARY.labels(
                    account=self.name,
                    dimension_key=dimension_key,
                    dimension_value=dimension_value,
                    summary_type='official_amount'
                ).set(official_amount_by_costs)
                
        except exceptions.ClientRequestException as e:
            logger.error(f"Error collecting LISTCosts metrics for account {self.name}: "
                         f"status_code={e.status_code}, request_id={e.request_id}, "
                         f"error_code={e.error_code}, error_msg={e.error_msg}")
        except Exception as e:
            import traceback
            logger.error(f"Error collecting LISTCosts metrics for account {self.name}: {e}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
        logger.debug(f"Completed LISTCOSTS metrics collection for account {self.name}")
            
    def describe(self):
        """
        描述此收集器提供的指标
        """
        logger.debug("Describing LISTCOSTS collector metrics")
        return [
            COST_AMOUNT,
            OFFICIAL_COST_AMOUNT,
            COST_SUMMARY
        ]