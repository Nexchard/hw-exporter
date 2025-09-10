import time
import threading
import yaml
from prometheus_client import start_http_server, Gauge, Counter, Histogram
import logging
import os
import importlib

# 配置日志 - 初始设置，后续会从配置文件中覆盖
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 创建logger实例
logger = logging.getLogger(__name__)

# 自监控指标
COLLECTOR_UP = Gauge(
    'exporter_collector_up',
    'Whether the collector is up and running',
    ['collector', 'account']
)

COLLECTOR_SCRAPE_DURATION = Histogram(
    'exporter_collector_scrape_duration_seconds',
    'Duration of collector scrapes',
    ['collector', 'account']
)

SCRAPE_ERRORS_TOTAL = Counter(
    'exporter_scrape_errors_total',
    'Total number of scrape errors',
    ['collector', 'account', 'error_type']
)


class HuaweiCloudExporter:
    """
    华为云Exporter主程序
    """
    
    def __init__(self, config_path='config/config.yaml'):
        """
        初始化Exporter
        
        :param config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.collectors = []
        self.threads = []
        # 从配置文件设置日志级别
        log_level_str = self.config.get('exporter', {}).get('log_level', 'INFO')
        log_level = getattr(logging, log_level_str.upper(), logging.INFO)
        logging.getLogger().setLevel(log_level)
        logger.setLevel(log_level)
        
        logger.debug(f"Initializing HuaweiCloudExporter with config path: {config_path}")
        logger.debug(f"Log level set to: {log_level_str}")
        
    def _load_config(self, config_path):
        """
        加载配置文件
        
        :param config_path: 配置文件路径
        :return: 配置对象
        """
        logger.debug(f"Loading configuration from {config_path}")
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        logger.debug("Configuration loaded successfully")
        logger.info(f"Found {len(config.get('huawei_cloud_accounts', []))} Huawei Cloud accounts in configuration")
        return config
            
    def _setup_collectors(self):
        """
        设置指标收集器
        """
        logger.debug("Setting up collectors")
        for account in self.config['huawei_cloud_accounts']:
            account_name = account['name']
            logger.info(f"Setting up collectors for account: {account_name}")
            
            # 根据启用的模块动态创建收集器
            for module_name, module_config in account['modules'].items():
                if module_config.get('enabled', False):
                    logger.debug(f"Attempting to create collector {module_name} for account {account_name}")
                    try:
                        # 动态导入对应的收集器类
                        module = importlib.import_module(f'collectors.{module_name}_metrics')
                        collector_class = getattr(module, f'{module_name.upper()}Collector')
                        
                        # 创建收集器实例
                        collector = collector_class(account_name, account, module_config)
                        self.collectors.append(collector)
                        logger.info(f"Successfully created {module_name} collector for account: {account_name}")
                        logger.debug(f"Collector {module_name} config: {module_config}")
                        
                        # 初始化自监控指标
                        COLLECTOR_UP.labels(collector=module_name, account=account_name).set(1)
                    except (ImportError, AttributeError) as e:
                        logger.error(f"Failed to create {module_name} collector for account {account_name}: {e}")
                        SCRAPE_ERRORS_TOTAL.labels(
                            collector=module_name, 
                            account=account_name, 
                            error_type='import_error'
                        ).inc()
                    except Exception as e:
                        logger.error(f"Unexpected error creating {module_name} collector for account {account_name}: {e}")
                        SCRAPE_ERRORS_TOTAL.labels(
                            collector=module_name, 
                            account=account_name, 
                            error_type='unexpected_error'
                        ).inc()
                else:
                    logger.debug(f"Module {module_name} is disabled for account {account_name}")
        logger.debug(f"Finished setting up collectors. Total collectors: {len(self.collectors)}")
            
    def _collect_metrics(self):
        """
        收集所有指标
        """
        logger.debug("Starting metrics collection loop")
        while True:
            try:
                # 记录开始时间
                start_time = time.time()
                logger.debug(f"Starting collection cycle at {start_time}")
                
                # 执行所有收集器的collect方法
                for collector in self.collectors:
                    module_name = collector.__class__.__name__.replace('Collector', '').lower()
                    account_name = collector.name
                    
                    try:
                        logger.debug(f"Collecting metrics from {module_name} for account {account_name}")
                        with COLLECTOR_SCRAPE_DURATION.labels(collector=module_name, account=account_name).time():
                            collector.collect()
                        # 收集成功，设置状态为1
                        COLLECTOR_UP.labels(collector=module_name, account=account_name).set(1)
                        logger.debug(f"Successfully collected metrics from {module_name} for account {account_name}")
                    except Exception as e:
                        logger.error(f"Error collecting metrics from {module_name} for account {account_name}: {e}")
                        # 收集失败，设置状态为0
                        COLLECTOR_UP.labels(collector=module_name, account=account_name).set(0)
                        SCRAPE_ERRORS_TOTAL.labels(
                            collector=module_name, 
                            account=account_name, 
                            error_type='collection_error'
                        ).inc()
                
                # 计算执行时间
                execution_time = time.time() - start_time
                logger.debug(f"Collection cycle completed in {execution_time:.2f} seconds")
                
                # 获取所有收集器中最小的collection_interval值作为采集间隔
                if self.collectors:
                    min_interval = min(collector.collection_interval for collector in self.collectors)
                    # 确保睡眠时间不为负数
                    sleep_time = max(min_interval - execution_time, 0)
                    logger.info(f"Metrics collection took {execution_time:.2f} seconds, sleeping for {sleep_time:.2f} seconds")
                    logger.debug(f"Next collection cycle in {sleep_time:.2f} seconds")
                    time.sleep(sleep_time)
                else:
                    # 如果没有收集器，使用默认间隔
                    logger.debug("No collectors configured, sleeping for 60 seconds")
                    time.sleep(60)
            except Exception as e:
                logger.error(f"Error collecting metrics: {e}")
                # 出现错误时等待一段时间再重试
                logger.debug("Sleeping for 60 seconds after error")
                time.sleep(60)
                
    def start(self):
        """
        启动Exporter
        """
        logger.info("Starting Huawei Cloud Exporter")
        # 设置收集器
        self._setup_collectors()
        
        # 启动指标收集线程
        collect_thread = threading.Thread(target=self._collect_metrics, daemon=True)
        collect_thread.start()
        self.threads.append(collect_thread)
        logger.debug("Metrics collection thread started")
        
        # 启动Prometheus HTTP服务器
        port = self.config['exporter'].get('port', 9091)
        address = self.config['exporter'].get('address', '0.0.0.0')
        
        logger.info(f"Starting Prometheus exporter on {address}:{port}")
        start_http_server(port, addr=address)
        logger.debug(f"Prometheus HTTP server started on {address}:{port}")
        
        # 保持程序运行
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down exporter...")
            # 清理资源
            for thread in self.threads:
                if thread.is_alive():
                    thread.join(timeout=5)


if __name__ == '__main__':
    exporter = HuaweiCloudExporter()
    exporter.start()