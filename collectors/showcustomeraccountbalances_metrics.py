from collectors.base_collector import BaseCollector
from prometheus_client import Gauge
import logging
import os

# 导入华为云SDK相关模块
from huaweicloudsdkcore.auth.credentials import GlobalCredentials
from huaweicloudsdkbss.v2.region.bss_region import BssRegion
from huaweicloudsdkcore.exceptions import exceptions
from huaweicloudsdkbss.v2 import *

logger = logging.getLogger(__name__)

# 定义模块级指标，避免重复注册
# 账户总欠款金额指标
DEBT_AMOUNT = Gauge(
    'huaweicloud_bss_debt_amount',
    'Total debt amount in BSS',
    ['account', 'currency']
)

# 账户余额指标
ACCOUNT_BALANCE = Gauge(
    'huaweicloud_bss_account_balance',
    'Account balance in BSS',
    ['account', 'account_id', 'account_type', 'currency']
)

# 账户专款专用余额指标
ACCOUNT_DESIGNATED_AMOUNT = Gauge(
    'huaweicloud_bss_account_designated_amount',
    'Account designated amount in BSS',
    ['account', 'account_id', 'account_type', 'currency']
)

# 账户信用额度指标
ACCOUNT_CREDIT_AMOUNT = Gauge(
    'huaweicloud_bss_account_credit_amount',
    'Account credit amount in BSS (only for credit accounts)',
    ['account', 'account_id', 'account_type', 'currency']
)

# 账户总金额度指标
ACCOUNT_TOTAL_AMOUNT = Gauge(
    'huaweicloud_bss_account_total_amount',
    'Total amount in BSS account (balance + designated_amount + credit_amount)',
    ['account', 'account_id', 'account_type', 'currency']
)


class SHOWCUSTOMERACCOUNTBALANCESCollector(BaseCollector):
    """
    ShowCustomerAccountBalances API指标收集器
    用于收集华为云账户余额信息
    专门使用AK/SK认证方式和华为云SDK
    """
    
    def __init__(self, name, account_config, module_config=None):
        super().__init__(name, account_config, module_config)
        
        # 初始化华为云BSS客户端
        logger.debug(f"Initializing SHOWCUSTOMERACCOUNTBALANCES collector for account {name}")
        try:
            # 使用配置中的AK/SK或者环境变量
            ak = self.ak or os.environ.get("CLOUD_SDK_AK")
            sk = self.sk or os.environ.get("CLOUD_SDK_SK")
            
            if not ak or not sk:
                logger.error(f"Missing AK/SK credentials for SHOWCUSTOMERACCOUNTBALANCES collector in account {self.name}")
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
        收集ShowCustomerAccountBalances API指标
        """
        logger.debug(f"Starting SHOWCUSTOMERACCOUNTBALANCES metrics collection for account {self.name}")
        if not self.client:
            logger.warning(f"BSS client not initialized for SHOWCUSTOMERACCOUNTBALANCES collector in account {self.name}")
            return
            
        try:
            # 构造请求参数
            request = ShowCustomerAccountBalancesRequest()
            logger.debug("ShowCustomerAccountBalancesRequest object created")
            
            # 调用华为云API
            logger.debug("Calling show_customer_account_balances API")
            response = self.client.show_customer_account_balances(request)
            logger.debug("show_customer_account_balances API call successful")
            
            # 解析响应数据
            data = response.to_json_object()
            logger.debug(f"Response data keys: {data.keys()}")
            
            # 获取债务金额
            debt_amount = data.get('debt_amount', 0)
            currency = data.get('currency', 'CNY')
            
            # 更新总欠款金额指标
            DEBT_AMOUNT.labels(
                account=self.name,
                currency=currency
            ).set(debt_amount)
            logger.debug(f"Account {self.name} debt amount: {debt_amount} {currency}")
            
            # 解析账户余额列表数据并更新指标
            account_balances = data.get('account_balances', [])
            logger.debug(f"Found {len(account_balances)} account balances")
            
            # 如果没有账户余额信息，也要确保指标被设置为0
            if not account_balances:
                logger.info(f"No account balances found for account {self.name}")
                # 不需要显式设置为0，因为新指标默认为0，但记录日志即可
            
            # 更新每个账户的详细指标
            for account in account_balances:
                account_id = account.get('account_id', 'unknown')
                account_type = self._get_account_type_name(account.get('account_type', 0))
                currency = account.get('currency', 'CNY')
                
                logger.debug(f"Processing account balance: {account_id}, type: {account_type}")
                
                # 账户余额
                amount = account.get('amount', 0)
                ACCOUNT_BALANCE.labels(
                    account=self.name,
                    account_id=account_id,
                    account_type=account_type,
                    currency=currency
                ).set(amount)
                logger.debug(f"Account {account_id} balance: {amount} {currency}")
                
                # 专款专用余额
                designated_amount = account.get('designated_amount', 0)
                ACCOUNT_DESIGNATED_AMOUNT.labels(
                    account=self.name,
                    account_id=account_id,
                    account_type=account_type,
                    currency=currency
                ).set(designated_amount)
                logger.debug(f"Account {account_id} designated amount: {designated_amount} {currency}")
                
                # 信用额度（仅信用账户存在该字段）
                credit_amount = account.get('credit_amount', 0)
                ACCOUNT_CREDIT_AMOUNT.labels(
                    account=self.name,
                    account_id=account_id,
                    account_type=account_type,
                    currency=currency
                ).set(credit_amount)
                logger.debug(f"Account {account_id} credit amount: {credit_amount} {currency}")
                
                # 账户总金额度（余额+专款专用余额+信用额度）
                total_amount = amount + designated_amount + credit_amount
                ACCOUNT_TOTAL_AMOUNT.labels(
                    account=self.name,
                    account_id=account_id,
                    account_type=account_type,
                    currency=currency
                ).set(total_amount)
                logger.debug(f"Account {account_id} total amount: {total_amount} {currency}")
                
        except exceptions.ClientRequestException as e:
            logger.error(f"Error collecting SHOWCUSTOMERACCOUNTBALANCES metrics for account {self.name}: "
                         f"status_code={e.status_code}, request_id={e.request_id}, "
                         f"error_code={e.error_code}, error_msg={e.error_msg}")
        except Exception as e:
            import traceback
            logger.error(f"Error collecting SHOWCUSTOMERACCOUNTBALANCES metrics for account {self.name}: {e}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
        logger.debug(f"Completed SHOWCUSTOMERACCOUNTBALANCES metrics collection for account {self.name}")
            
    def _get_account_type_name(self, account_type):
        """
        根据账户类型ID获取账户类型名称
            
        :param account_type: 账户类型ID
        :return: 账户类型名称
        """
        # 账户类型映射
        type_map = {
            1: 'balance',      # 余额账户
            2: 'credit',       # 信用账户
            5: 'bonus',        # 奖励金账户
            7: 'deposit'       # 保证金账户
        }
        account_type_name = type_map.get(account_type, f'unknown_type_{account_type}')
        logger.debug(f"Mapped account type {account_type} to {account_type_name}")
        return account_type_name
                
    def describe(self):
        """
        描述此收集器提供的指标
        """
        logger.debug("Describing SHOWCUSTOMERACCOUNTBALANCES collector metrics")
        return [
            DEBT_AMOUNT,
            ACCOUNT_BALANCE,
            ACCOUNT_DESIGNATED_AMOUNT,
            ACCOUNT_CREDIT_AMOUNT,
            ACCOUNT_TOTAL_AMOUNT
        ]