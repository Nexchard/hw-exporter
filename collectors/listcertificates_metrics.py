from collectors.base_collector import BaseCollector
from prometheus_client import Gauge, Info
import logging
import os
from datetime import datetime
import time

# 导入华为云SDK相关模块
from huaweicloudsdkcore.auth.credentials import GlobalCredentials
from huaweicloudsdkscm.v3.region.scm_region import ScmRegion
from huaweicloudsdkcore.exceptions import exceptions
from huaweicloudsdkscm.v3 import *

logger = logging.getLogger(__name__)

# 定义模块级指标，避免重复注册
# 证书总数指标
CERTIFICATE_TOTAL_COUNT = Gauge(
    'huaweicloud_scm_certificate_total_count',
    'Total count of certificates in SCM',
    ['account']
)

# 证书状态指标
CERTIFICATE_STATUS = Gauge(
    'huaweicloud_scm_certificate_status',
    'Status of certificates in SCM (1: ISSUED, 0: others)',
    ['account', 'certificate_id', 'domain']
)

# 证书过期时间指标 (Unix时间戳)
CERTIFICATE_EXPIRE_TIMESTAMP = Gauge(
    'huaweicloud_scm_certificate_expire_timestamp',
    'Expire timestamp of certificates in SCM (Unix timestamp)',
    ['account', 'certificate_id', 'domain']
)

# 证书信息指标
CERTIFICATE_INFO = Info(
    'huaweicloud_scm_certificate',
    'Detailed information of certificates in SCM',
    ['account', 'certificate_id']
)


class LISTCERTIFICATESCollector(BaseCollector):
    """
    ListCertificates API指标收集器
    用于收集华为云SSL证书信息
    专门使用AK/SK认证方式和华为云SDK
    """
    
    def __init__(self, name, account_config, module_config=None):
        super().__init__(name, account_config, module_config)
        
        # 初始化华为云SCM客户端
        logger.debug(f"Initializing LISTCERTIFICATES collector for account {name}")
        try:
            # 使用配置中的AK/SK或者环境变量
            ak = self.ak or os.environ.get("CLOUD_SDK_AK")
            sk = self.sk or os.environ.get("CLOUD_SDK_SK")
            
            if not ak or not sk:
                logger.error(f"Missing AK/SK credentials for LISTCERTIFICATES collector in account {self.name}")
                self.client = None
                return
                
            credentials = GlobalCredentials(ak, sk)
            logger.debug("GlobalCredentials created successfully")
            
            # 使用配置中的区域或者默认区域
            region = self.region or "cn-north-4"
            logger.debug(f"Using region: {region}")
            
            self.client = ScmClient.new_builder() \
                .with_credentials(credentials) \
                .with_region(ScmRegion.value_of(region)) \
                .build()
            logger.debug("SCM client initialized successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize SCM client for account {self.name}: {e}")
            self.client = None

    def collect(self):
        """
        收集ListCertificates API指标
        """
        logger.debug(f"Starting LISTCERTIFICATES metrics collection for account {self.name}")
        if not self.client:
            logger.warning(f"SCM client not initialized for LISTCERTIFICATES collector in account {self.name}")
            return
            
        try:
            # 构造请求参数
            request = ListCertificatesRequest()
            logger.debug("ListCertificatesRequest object created")
            
            # 从配置中获取请求参数
            if self.params:
                logger.debug(f"Applying parameters: {self.params}")
                if 'limit' in self.params:
                    request.limit = self.params['limit']
                    logger.debug(f"Set limit to {request.limit}")
                if 'offset' in self.params:
                    request.offset = self.params['offset']
                    logger.debug(f"Set offset to {request.offset}")
                if 'sort_dir' in self.params:
                    request.sort_dir = self.params['sort_dir']
                    logger.debug(f"Set sort_dir to {request.sort_dir}")
                if 'sort_key' in self.params:
                    request.sort_key = self.params['sort_key']
                    logger.debug(f"Set sort_key to {request.sort_key}")
                if 'status' in self.params:
                    request.status = self.params['status']
                    logger.debug(f"Set status to {request.status}")
                if 'enterprise_project_id' in self.params:
                    request.enterprise_project_id = self.params['enterprise_project_id']
                    logger.debug(f"Set enterprise_project_id to {request.enterprise_project_id}")
                if 'deploy_support' in self.params:
                    request.deploy_support = self.params['deploy_support']
                    logger.debug(f"Set deploy_support to {request.deploy_support}")
                if 'owned_by_self' in self.params:
                    request.owned_by_self = self.params['owned_by_self']
                    logger.debug(f"Set owned_by_self to {request.owned_by_self}")
                if 'expired_days_since' in self.params:
                    request.expired_days_since = self.params['expired_days_since']
                    logger.debug(f"Set expired_days_since to {request.expired_days_since}")
            
            # 调用华为云API
            logger.debug("Calling list_certificates API")
            response = self.client.list_certificates(request)
            logger.debug("list_certificates API call successful")
            
            # 解析响应数据
            data = response.to_json_object()
            logger.debug(f"Response data keys: {data.keys()}")
            
            # 获取证书总数
            total_count = data.get('total_count', 0)
            CERTIFICATE_TOTAL_COUNT.labels(account=self.name).set(total_count)
            logger.debug(f"Total certificates count: {total_count}")
            
            # 解析证书列表数据并更新指标
            certificates = data.get('certificates', [])
            logger.debug(f"Found {len(certificates)} certificates")
            
            # 更新每个证书的详细指标
            for cert in certificates:
                certificate_id = cert.get('id', 'unknown')
                domain = cert.get('domain', 'unknown')
                status = cert.get('status', 'unknown')
                expire_time = cert.get('expire_time', '')
                
                logger.debug(f"Processing certificate: {certificate_id}, domain: {domain}")
                
                # 证书状态指标 (1表示ISSUED状态，0表示其他状态)
                status_value = 1 if status == 'ISSUED' else 0
                CERTIFICATE_STATUS.labels(
                    account=self.name,
                    certificate_id=certificate_id,
                    domain=domain
                ).set(status_value)
                logger.debug(f"Certificate {certificate_id} status: {status} -> {status_value}")
                
                # 证书过期时间戳
                expire_timestamp = 0
                if expire_time:
                    try:
                        # 将'YYYY-MM-DD HH:MM:SS.S'格式转换为时间戳
                        dt = datetime.strptime(expire_time.split('.')[0], '%Y-%m-%d %H:%M:%S')
                        expire_timestamp = int(time.mktime(dt.timetuple()))
                        logger.debug(f"Certificate {certificate_id} expire time: {expire_time} -> {expire_timestamp}")
                    except Exception as e:
                        logger.warning(f"Failed to parse expire time for certificate {certificate_id}: {e}")
                
                CERTIFICATE_EXPIRE_TIMESTAMP.labels(
                    account=self.name,
                    certificate_id=certificate_id,
                    domain=domain
                ).set(expire_timestamp)
                
                # 证书信息指标
                cert_info = {
                    'name': cert.get('name', ''),
                    'domain': cert.get('domain', ''),
                    'sans': cert.get('sans', ''),
                    'type': cert.get('type', ''),
                    'signature_algorithm': cert.get('signature_algorithm', ''),
                    'brand': cert.get('brand', ''),
                    'domain_type': cert.get('domain_type', ''),
                    'validity_period': str(cert.get('validity_period', '')),
                    'status': cert.get('status', ''),
                    'domain_count': str(cert.get('domain_count', '')),
                    'wildcard_count': str(cert.get('wildcard_count', ''))
                }
                CERTIFICATE_INFO.labels(
                    account=self.name,
                    certificate_id=certificate_id
                ).info(cert_info)
                logger.debug(f"Certificate {certificate_id} info updated")
                
        except exceptions.ClientRequestException as e:
            logger.error(f"Error collecting LISTCERTIFICATES metrics for account {self.name}: "
                         f"status_code={e.status_code}, request_id={e.request_id}, "
                         f"error_code={e.error_code}, error_msg={e.error_msg}")
        except Exception as e:
            import traceback
            logger.error(f"Error collecting LISTCERTIFICATES metrics for account {self.name}: {e}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
        logger.debug(f"Completed LISTCERTIFICATES metrics collection for account {self.name}")
            
    def describe(self):
        """
        描述此收集器提供的指标
        """
        logger.debug("Describing LISTCERTIFICATES collector metrics")
        return [
            CERTIFICATE_TOTAL_COUNT,
            CERTIFICATE_STATUS,
            CERTIFICATE_EXPIRE_TIMESTAMP,
            CERTIFICATE_INFO
        ]