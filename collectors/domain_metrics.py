from collectors.base_collector import BaseCollector
from prometheus_client import Gauge, Info
import logging
from utils.http_client import HTTPClient

logger = logging.getLogger(__name__)

# 定义模块级指标，避免重复注册
# 域名总数指标
DOMAIN_TOTAL_COUNT = Gauge(
    'huaweicloud_domain_total_count',
    'Total count of domains in the account',
    ['account']
)

# 域名状态指标
DOMAIN_STATUS = Gauge(
    'huaweicloud_domain_status',
    'Status of domains (1 for active, 0 for inactive)',
    ['account', 'domain_name']
)

# 域名注册日期指标 (Unix时间戳)
DOMAIN_REGISTER_TIMESTAMP = Gauge(
    'huaweicloud_domain_register_timestamp',
    'Register timestamp of domains (Unix timestamp)',
    ['account', 'domain_name']
)

# 域名到期时间指标 (Unix时间戳)
DOMAIN_EXPIRE_TIMESTAMP = Gauge(
    'huaweicloud_domain_expire_timestamp',
    'Expire timestamp of domains (Unix timestamp)',
    ['account', 'domain_name']
)

# 域名信息指标
DOMAIN_INFO = Info(
    'huaweicloud_domain',
    'Detailed information of domains',
    ['account', 'domain_name']
)

# 域名剩余天数指标
DOMAIN_REMAINING_DAYS = Gauge(
    'huaweicloud_domain_remaining_days',
    'Remaining days until domain expires',
    ['account', 'domain_name']
)

# 域名是否启用隐私保护指标
DOMAIN_PRIVACY_PROTECTION = Gauge(
    'huaweicloud_domain_privacy_protection',
    'Whether privacy protection is enabled for the domain (1 for enabled, 0 for disabled)',
    ['account', 'domain_name']
)

# 域名是否自动续费指标
DOMAIN_AUTO_RENEW = Gauge(
    'huaweicloud_domain_auto_renew',
    'Whether auto renew is enabled for the domain (1 for enabled, 0 for disabled)',
    ['account', 'domain_name']
)


class DOMAINCollector(BaseCollector):
    """
    域名信息收集器
    用于收集华为云账户中的域名信息
    """
    
    def __init__(self, name, account_config, module_config=None):
        super().__init__(name, account_config, module_config)
        
        # 设置默认端点（如果模块配置中没有指定）
        if not self.endpoint:
            self.endpoint = "https://domain.myhuaweicloud.com"
            
        if not self.iam_endpoint:
            self.iam_endpoint = "https://iam.myhuaweicloud.com"
            
        # 初始化HTTP客户端
        self.http_client = HTTPClient()
        
        logger.debug(f"DOMAINCollector initialized for account {name}")
        logger.debug(f"Endpoint: {self.endpoint}")
        logger.debug(f"IAM Endpoint: {self.iam_endpoint}")

    def collect(self):
        """
        收集域名信息指标
        """
        logger.debug(f"Starting domain metrics collection for account {self.name}")
        try:
            # 获取所有域名信息
            logger.debug("Fetching all domains")
            all_domains_result = self.get_all_domains()
            
            if not all_domains_result["success"]:
                logger.error(f"Failed to get domain information for account {self.name}: {all_domains_result.get('message', 'Unknown error')}")
                return
                
            domain_data = all_domains_result["data"]
            domains = domain_data.get("domains", [])
            total_count = domain_data.get("total", 0)
            
            logger.debug(f"Retrieved {len(domains)} domains, total count: {total_count}")
            
            # 更新域名总数指标
            DOMAIN_TOTAL_COUNT.labels(account=self.name).set(total_count)
            logger.debug(f"Updated total domain count for account {self.name}: {total_count}")
            
            # 如果没有域名，也要确保指标被设置
            if not domains:
                logger.info(f"No domains found for account {self.name}")
                return
                
            # 更新每个域名的详细指标
            for domain in domains:
                domain_name = domain.get('domain_name', 'unknown')
                logger.debug(f"Processing domain: {domain_name}")
                
                # 域名状态指标 (将状态字符串转换为0/1)
                status = domain.get('status', 'UNKNOWN')
                # 假设'REALNAMEVERIFY'和'NORMAL'表示正常状态
                status_value = 1 if status in ['REALNAMEVERIFY', 'NORMAL'] else 0
                DOMAIN_STATUS.labels(
                    account=self.name,
                    domain_name=domain_name
                ).set(status_value)
                logger.debug(f"Domain {domain_name} status: {status} -> {status_value}")
                
                # 域名注册日期指标
                register_date = domain.get('register_date')
                if register_date:
                    try:
                        import datetime
                        register_datetime = datetime.datetime.strptime(register_date, '%Y-%m-%d')
                        register_timestamp = register_datetime.timestamp()
                        DOMAIN_REGISTER_TIMESTAMP.labels(
                            account=self.name,
                            domain_name=domain_name
                        ).set(register_timestamp)
                        logger.debug(f"Domain {domain_name} register date: {register_date} -> {register_timestamp}")
                    except Exception as e:
                        logger.warning(f"Failed to parse register date for domain {domain_name}: {e}")
                
                # 域名到期时间指标
                expire_date = domain.get('expire_date')
                if expire_date:
                    try:
                        import datetime
                        expire_datetime = datetime.datetime.strptime(expire_date, '%Y-%m-%d')
                        expire_timestamp = expire_datetime.timestamp()
                        DOMAIN_EXPIRE_TIMESTAMP.labels(
                            account=self.name,
                            domain_name=domain_name
                        ).set(expire_timestamp)
                        logger.debug(f"Domain {domain_name} expire date: {expire_date} -> {expire_timestamp}")
                        
                        # 计算并更新剩余天数指标
                        remaining_days = (expire_datetime - datetime.datetime.now()).days
                        DOMAIN_REMAINING_DAYS.labels(
                            account=self.name,
                            domain_name=domain_name
                        ).set(remaining_days)
                        logger.debug(f"Domain {domain_name} remaining days: {remaining_days}")
                    except Exception as e:
                        logger.warning(f"Failed to parse expire date for domain {domain_name}: {e}")
                
                # 域名隐私保护指标
                privacy_protection = domain.get('privacy_protection', False)
                DOMAIN_PRIVACY_PROTECTION.labels(
                    account=self.name,
                    domain_name=domain_name
                ).set(1 if privacy_protection else 0)
                logger.debug(f"Domain {domain_name} privacy protection: {privacy_protection}")
                
                # 域名自动续费指标
                auto_renew = domain.get('auto_renew', '0')
                DOMAIN_AUTO_RENEW.labels(
                    account=self.name,
                    domain_name=domain_name
                ).set(1 if auto_renew == '1' else 0)
                logger.debug(f"Domain {domain_name} auto renew: {auto_renew}")
                
                # 域名信息指标
                DOMAIN_INFO.labels(
                    account=self.name,
                    domain_name=domain_name
                ).info({
                    'reg_type': domain.get('reg_type', ''),
                    'audit_status': domain.get('audit_status', ''),
                    'audit_fail_reason': domain.get('audit_fail_reason', '') or '',
                    'transfer_status': domain.get('transfer_status', '') or '',
                    'order_id': domain.get('order_id', '') or ''
                })
                logger.debug(f"Domain {domain_name} info updated")
                        
        except Exception as e:
            logger.error(f"Error collecting domain metrics for account {self.name}: {e}")
        logger.debug(f"Completed domain metrics collection for account {self.name}")
            
    def query_domains(self, offset=0, limit=200):
        """
        查询域名列表
        :param offset: 偏移量
        :param limit: 每页数量
        :return: 查询结果字典
        """
        logger.debug(f"Querying domains for account {self.name} with offset={offset}, limit={limit}")
        try:
            # 使用统一的HTTP客户端发送请求
            url = f"{self.endpoint}/v2/domains"
            params = {
                "offset": offset,
                "limit": limit
            }
            
            logger.debug(f"Sending GET request to {url} with params {params}")
            response = self.http_client.get(
                url,
                auth_type='token',
                iam_endpoint=self.iam_endpoint,
                domain_name=self.domain_name,
                username=self.username,
                password=self.password,
                params=params
            )
            
            data = response.json()
            domains_count = len(data.get("domains", []))
            logger.debug(f"Successfully queried {domains_count} domains")
            return {
                "success": True,
                "data": {
                    "domains": data.get("domains", []),
                    "total": data.get("total", 0)
                }
            }
        except Exception as e:
            logger.error(f"Exception while querying domains for account {self.name}: {str(e)}")
            return {"success": False, "data": None, "message": str(e)}
    
    def get_all_domains(self):
        """
        获取所有域名信息
        :return: 所有域名信息字典
        """
        logger.debug(f"Getting all domains for account {self.name}")
        all_domains = []
        offset = 0
        limit = self.params.get('limit', 200)  # 从配置中获取limit参数，默认200
        logger.debug(f"Using limit: {limit}")
        
        while True:
            logger.debug(f"Fetching domains batch: offset={offset}")
            result = self.query_domains(offset, limit)
            if not result["success"]:
                logger.error(f"Failed to get domains batch for account {self.name}")
                return result
            
            domains = result["data"]["domains"]
            total = result["data"]["total"]
            all_domains.extend(domains)
            logger.debug(f"Retrieved {len(domains)} domains in this batch")
            
            # 如果当前获取的域名数量小于limit，说明已经获取完所有域名
            if len(domains) < limit:
                logger.debug("All domains fetched")
                break
            
            offset += limit
            logger.debug(f"Updating offset to {offset}")
        
        logger.debug(f"Total domains retrieved: {len(all_domains)}")
        return {
            "success": True,
            "data": {
                "domains": all_domains,
                "total": len(all_domains)
            }
        }
            
    def describe(self):
        """
        描述此收集器提供的指标
        """
        logger.debug("Describing DOMAIN collector metrics")
        return [
            DOMAIN_TOTAL_COUNT,
            DOMAIN_STATUS,
            DOMAIN_REGISTER_TIMESTAMP,
            DOMAIN_EXPIRE_TIMESTAMP,
            DOMAIN_INFO,
            DOMAIN_REMAINING_DAYS,
            DOMAIN_PRIVACY_PROTECTION,
            DOMAIN_AUTO_RENEW
        ]