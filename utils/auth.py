import hmac
import hashlib
import datetime
import requests
import logging

logger = logging.getLogger(__name__)

class HWSAuth:
    """
    华为云API认证工具类
    """
    
    @staticmethod
    def get_aksk_auth_headers(ak, sk, region, service):
        """
        生成华为云API AK/SK认证头
        
        :param ak: Access Key ID
        :param sk: Secret Access Key
        :param region: 区域
        :param service: 服务名称
        :return: 认证头字典
        """
        logger.debug(f"Generating AK/SK auth headers for service: {service}, region: {region}")
        
        # 获取当前UTC时间
        utcnow = datetime.datetime.utcnow()
        amzdate = utcnow.strftime('%Y%m%dT%H%M%SZ')
        datestamp = utcnow.strftime('%Y%m%d')
        
        logger.debug(f"Current UTC time: {utcnow}, date stamp: {datestamp}")
        
        # 创建签名密钥
        signing_key = HWSAuth.getSignatureKey(sk, datestamp, region, service)
        logger.debug("Signature key generated successfully")
        
        # 构建需要签名的字符串
        http_method = 'GET'
        canonical_uri = '/'
        canonical_querystring = ''
        canonical_headers = f'host:service.{region}.huaweicloud.com\nx-sdk-date:{amzdate}\n'
        signed_headers = 'host;x-sdk-date'
        
        # 构建规范请求
        payload_hash = hashlib.sha256(('').encode('utf-8')).hexdigest()
        canonical_request = f'{http_method}\n{canonical_uri}\n{canonical_querystring}\n{canonical_headers}\n{signed_headers}\n{payload_hash}'
        
        # 创建字符串签名
        canonical_request_hash = hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()
        string_to_sign = f'SDK-HMAC-SHA256\n{amzdate}\n{datestamp}/{region}/{service}/sdk_request\n{canonical_request_hash}'
        
        logger.debug(f"String to sign: {string_to_sign}")
        
        # 计算签名
        signature = hmac.new(signing_key, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()
        logger.debug("Signature calculated successfully")
        
        # 构造认证头
        headers = {
            'X-Sdk-Date': amzdate,
            'Authorization': f'SDK-HMAC-SHA256 Credential={ak}/{datestamp}/{region}/{service}/sdk_request, SignedHeaders={signed_headers}, Signature={signature}'
        }
        
        logger.debug("AK/SK auth headers generated successfully")
        return headers
        
    @staticmethod
    def get_token_auth_headers(iam_endpoint, domain_name, username, password, project_id=None):
        """
        通过用户名/密码获取Token，并生成认证头
        
        :param iam_endpoint: IAM端点
        :param domain_name: 账号名
        :param username: 用户名
        :param password: 密码
        :param project_id: 项目ID（可选）
        :return: 认证头字典
        """
        logger.debug(f"Getting token auth headers from IAM endpoint: {iam_endpoint}")
        logger.debug(f"Domain: {domain_name}, Username: {username}, Project ID: {project_id}")
        
        try:
            # 构造获取Token的请求
            auth_url = f"{iam_endpoint}/v3/auth/tokens"
            logger.debug(f"Auth URL: {auth_url}")
            
            # 构造请求体
            auth_data = {
                "auth": {
                    "identity": {
                        "methods": ["password"],
                        "password": {
                            "user": {
                                "name": username,
                                "password": password,
                                "domain": {
                                    "name": domain_name
                                }
                            }
                        }
                    }
                }
            }
            
            # 如果指定了project_id，则添加scope
            if project_id:
                auth_data["auth"]["scope"] = {
                    "project": {
                        "id": project_id
                    }
                }
                logger.debug(f"Added project scope with ID: {project_id}")
            
            logger.debug("Sending request to get token")
            # 发送请求获取Token
            response = requests.post(auth_url, json=auth_data)
            response.raise_for_status()
            
            # 从响应头中获取Token
            token = response.headers.get('X-Subject-Token')
            logger.debug("Token retrieved successfully")
            
            # 构造认证头
            headers = {
                'X-Auth-Token': token
            }
            
            logger.debug("Token auth headers generated successfully")
            return headers
            
        except Exception as e:
            logger.error(f"Failed to get token: {e}")
            return {}
        
    @staticmethod
    def sign(key, msg):
        """
        使用HMAC-SHA256算法签名
        
        :param key: 密钥
        :param msg: 消息
        :return: 签名结果
        """
        logger.debug(f"Signing message with key length: {len(key) if key else 0}")
        result = hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()
        logger.debug("Message signed successfully")
        return result
        
    @staticmethod
    def getSignatureKey(key, dateStamp, regionName, serviceName):
        """
        生成签名密钥
        
        :param key: 原始密钥
        :param dateStamp: 日期戳
        :param regionName: 区域名称
        :param serviceName: 服务名称
        :return: 签名密钥
        """
        logger.debug(f"Generating signature key for date: {dateStamp}, region: {regionName}, service: {serviceName}")
        kDate = HWSAuth.sign(('SDK' + key).encode('utf-8'), dateStamp)
        kRegion = HWSAuth.sign(kDate, regionName)
        kService = HWSAuth.sign(kRegion, serviceName)
        kSigning = HWSAuth.sign(kService, 'sdk_request')
        logger.debug("Signature key generated successfully")
        return kSigning