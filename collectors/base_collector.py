from abc import ABC, abstractmethod
from prometheus_client import CollectorRegistry
import re
import logging

logger = logging.getLogger(__name__)


class BaseCollector(ABC):
    """
    采集器基类，所有具体的华为云服务采集器都应该继承此类
    """
    
    def __init__(self, name, account_config, module_config=None):
        """
        初始化采集器
        
        :param name: 采集器名称
        :param account_config: 账号配置信息
        :param module_config: 模块配置信息
        """
        self.name = name
        self.account_config = account_config
        self.module_config = module_config or {}
        
        logger.debug(f"Initializing BaseCollector for account {name}")
        
        # 认证信息 - 优先使用模块配置，否则使用账号配置
        self.ak = self.module_config.get('ak') or account_config['auth'].get('ak')
        self.sk = self.module_config.get('sk') or account_config['auth'].get('sk')
        self.domain_name = self.module_config.get('domain_name') or account_config['auth'].get('domain_name')
        self.username = self.module_config.get('username') or account_config['auth'].get('username')
        self.password = self.module_config.get('password') or account_config['auth'].get('password')
        self.iam_endpoint = self.module_config.get('iam_endpoint') or account_config['auth'].get('iam_endpoint')
        
        # 认证方式
        self.auth_type = self.module_config.get('auth_type', 'aksk')  # 默认使用AK/SK认证
        logger.debug(f"Authentication type: {self.auth_type}")
        
        # 项目和区域信息 - 优先使用模块配置，否则使用账号配置
        self.project_id = self.module_config.get('project_id') or account_config.get('auth', {}).get('project_id')
        self.region = self.module_config.get('region') or account_config.get('auth', {}).get('region')
        logger.debug(f"Project ID: {self.project_id}, Region: {self.region}")
        
        # API端点和参数 - 支持模板替换
        endpoint_template = self.module_config.get('endpoint', '')
        if endpoint_template and self.project_id:
            self.endpoint = endpoint_template.format(project_id=self.project_id)
        else:
            self.endpoint = self.module_config.get('endpoint', '')
            
        self.params = self.module_config.get('params', {})
        self.collection_interval = self._parse_time_interval(self.module_config.get('collection_interval', 60))
        
        logger.debug(f"Endpoint: {self.endpoint}")
        logger.debug(f"Parameters: {self.params}")
        logger.debug(f"Collection interval: {self.collection_interval} seconds")
        
    def _parse_time_interval(self, interval):
        """
        解析时间间隔配置，支持多种单位
        
        :param interval: 时间间隔配置，可以是数字（秒）或字符串（带单位）
        :return: 以秒为单位的时间间隔
        """
        logger.debug(f"Parsing time interval: {interval}")
        
        if isinstance(interval, (int, float)):
            # 如果是数字，直接作为秒数返回
            logger.debug(f"Interval is numeric, returning as seconds: {interval}")
            return interval
        elif isinstance(interval, str):
            # 如果是字符串，解析单位
            match = re.match(r'^(\d+(?:\.\d+)?)\s*([a-zA-Z]+)$', interval.strip())
            if match:
                value = float(match.group(1))
                unit = match.group(2).lower()
                logger.debug(f"Parsed value: {value}, unit: {unit}")
                
                if unit in ['s', 'sec', 'second', 'seconds']:
                    return value
                elif unit in ['m', 'min', 'minute', 'minutes']:
                    result = value * 60
                    logger.debug(f"Converted minutes to seconds: {result}")
                    return result
                elif unit in ['h', 'hr', 'hour', 'hours']:
                    result = value * 3600
                    logger.debug(f"Converted hours to seconds: {result}")
                    return result
                elif unit in ['d', 'day', 'days']:
                    result = value * 86400
                    logger.debug(f"Converted days to seconds: {result}")
                    return result
                else:
                    # 未知单位，默认作为秒处理
                    logger.debug(f"Unknown unit, treating as seconds: {value}")
                    return value
            else:
                # 没有单位的字符串，尝试转换为数字
                try:
                    result = float(interval)
                    logger.debug(f"String without unit converted to seconds: {result}")
                    return result
                except ValueError:
                    # 转换失败，返回默认值
                    logger.debug(f"Failed to convert string to number, returning default 60 seconds")
                    return 60
        else:
            # 其他类型，返回默认值
            logger.debug(f"Unknown type, returning default 60 seconds")
            return 60
        
    @abstractmethod
    def collect(self):
        """
        抽象方法，用于收集指标数据
        子类必须实现此方法
        """
        pass
        
    @abstractmethod
    def describe(self):
        """
        抽象方法，描述此收集器提供的指标
        子类必须实现此方法
        """
        pass