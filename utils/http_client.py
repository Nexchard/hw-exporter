import requests
import time
from utils.auth import HWSAuth
import logging

logger = logging.getLogger(__name__)


class HTTPClient:
    """
    HTTP客户端工具类，用于向华为云API发送请求
    """
    
    def __init__(self, timeout=30, retries=3):
        """
        初始化HTTP客户端
        
        :param timeout: 请求超时时间（秒）
        :param retries: 请求重试次数
        """
        self.timeout = timeout
        self.retries = retries
        self.session = requests.Session()
        
        logger.debug(f"HTTPClient initialized with timeout: {timeout}, retries: {retries}")
        
    def get(self, url, auth_type='aksk', ak=None, sk=None, iam_endpoint=None, domain_name=None, 
            username=None, password=None, project_id=None, region=None, service=None, params=None):
        """
        发送GET请求
        
        :param url: 请求URL
        :param auth_type: 认证方式 ('aksk' 或 'token')
        :param ak: Access Key ID (AK/SK认证所需)
        :param sk: Secret Access Key (AK/SK认证所需)
        :param iam_endpoint: IAM端点 (Token认证所需)
        :param domain_name: 账号名 (Token认证所需)
        :param username: 用户名 (Token认证所需)
        :param password: 密码 (Token认证所需)
        :param project_id: 项目ID
        :param region: 区域
        :param service: 服务名称
        :param params: 请求参数
        :return: 响应对象
        """
        logger.debug(f"Sending GET request to URL: {url}")
        logger.debug(f"Auth type: {auth_type}, Params: {params}")
        
        headers = {}
        if auth_type == 'aksk' and ak and sk and region and service:
            logger.debug(f"Using AK/SK auth for service: {service}, region: {region}")
            headers = HWSAuth.get_aksk_auth_headers(ak, sk, region, service)
        elif auth_type == 'token' and iam_endpoint and domain_name and username and password:
            logger.debug(f"Using Token auth with IAM endpoint: {iam_endpoint}")
            headers = HWSAuth.get_token_auth_headers(iam_endpoint, domain_name, username, password, project_id)
        else:
            logger.warning(f"Invalid authentication configuration for auth_type: {auth_type}")
        
        for attempt in range(self.retries):
            try:
                logger.debug(f"Attempt {attempt+1}/{self.retries} to send GET request")
                response = self.session.get(
                    url, 
                    headers=headers, 
                    params=params, 
                    timeout=self.timeout
                )
                logger.debug(f"GET request successful with status code: {response.status_code}")
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                logger.warning(f"Attempt {attempt+1}/{self.retries} failed: {e}")
                if attempt < self.retries - 1:
                    sleep_time = 2 ** attempt
                    logger.debug(f"Retrying in {sleep_time} seconds")
                    time.sleep(sleep_time)  # 指数退避
                else:
                    logger.error(f"All {self.retries} attempts failed. Raising exception.")
                    raise e
                    
    def post(self, url, auth_type='aksk', ak=None, sk=None, iam_endpoint=None, domain_name=None, 
             username=None, password=None, project_id=None, region=None, service=None, data=None, json=None):
        """
        发送POST请求
        
        :param url: 请求URL
        :param auth_type: 认证方式 ('aksk' 或 'token')
        :param ak: Access Key ID (AK/SK认证所需)
        :param sk: Secret Access Key (AK/SK认证所需)
        :param iam_endpoint: IAM端点 (Token认证所需)
        :param domain_name: 账号名 (Token认证所需)
        :param username: 用户名 (Token认证所需)
        :param password: 密码 (Token认证所需)
        :param project_id: 项目ID
        :param region: 区域
        :param service: 服务名称
        :param data: 表单数据
        :param json: JSON数据
        :return: 响应对象
        """
        logger.debug(f"Sending POST request to URL: {url}")
        logger.debug(f"Auth type: {auth_type}")
        logger.debug(f"Data: {data}, JSON: {json}")
        
        headers = {}
        if auth_type == 'aksk' and ak and sk and region and service:
            logger.debug(f"Using AK/SK auth for service: {service}, region: {region}")
            headers = HWSAuth.get_aksk_auth_headers(ak, sk, region, service)
        elif auth_type == 'token' and iam_endpoint and domain_name and username and password:
            logger.debug(f"Using Token auth with IAM endpoint: {iam_endpoint}")
            headers = HWSAuth.get_token_auth_headers(iam_endpoint, domain_name, username, password, project_id)
        else:
            logger.warning(f"Invalid authentication configuration for auth_type: {auth_type}")
        
        for attempt in range(self.retries):
            try:
                logger.debug(f"Attempt {attempt+1}/{self.retries} to send POST request")
                response = self.session.post(
                    url, 
                    headers=headers,
                    data=data,
                    json=json,
                    timeout=self.timeout
                )
                logger.debug(f"POST request successful with status code: {response.status_code}")
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                logger.warning(f"Attempt {attempt+1}/{self.retries} failed: {e}")
                if attempt < self.retries - 1:
                    sleep_time = 2 ** attempt
                    logger.debug(f"Retrying in {sleep_time} seconds")
                    time.sleep(sleep_time)  # 指数退避
                else:
                    logger.error(f"All {self.retries} attempts failed. Raising exception.")
                    raise e