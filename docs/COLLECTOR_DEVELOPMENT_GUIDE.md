# 华为云Exporter采集器开发指南

本文档详细说明如何向华为云Exporter项目添加新的采集器，包括设计原则、实现步骤、注意事项以及相关配置。

## 1. 项目架构概述

华为云Exporter采用模块化设计，支持多账号监控数据采集。主要组件包括：

- **配置管理**：加载和解析配置文件
- **认证模块**：处理华为云API认证逻辑
- **指标收集器**：每个云服务都有对应的收集器实现
- **主程序**：协调各组件工作

## 2. 采集器设计原则

### 2.1 基本要求

1. 所有采集器必须继承 `BaseCollector` 基类
2. 必须实现 `collect()` 和 `describe()` 抽象方法
3. 指标命名遵循 `huaweicloud_<服务名>_<指标名>` 格式
4. 使用模块级变量定义指标，避免重复注册

### 2.2 认证方式

项目支持两种认证方式：

1. **AK/SK认证**：适用于大部分华为云API
2. **Token认证**：适用于需要IAM token认证的API

### 2.3 错误处理

1. 添加完善的异常捕获机制
2. 记录详细的错误日志
3. 确保单个收集器出错不影响整个项目运行

## 3. 添加新采集器步骤

### 3.1 创建采集器文件

1. 在 `collectors/` 目录下创建新的采集器文件，命名格式为 `<模块名>_metrics.py`
2. 文件名应使用全小写，避免驼峰式命名

示例：创建ECS云服务器采集器
```bash
touch collectors/ecs_metrics.py
```

### 3.2 实现采集器类

``python
from collectors.base_collector import BaseCollector
from prometheus_client import Gauge
from utils.http_client import HTTPClient
import logging

logger = logging.getLogger(__name__)

# 模块级指标定义
ECS_COUNT = Gauge(
    'huaweicloud_ecs_total', 
    'Total number of ECS instances',
    ['account', 'region']
)

class EcsCollector(BaseCollector):
    """
    ECS云服务器指标采集器
    """
    
    def __init__(self, name, account_config, module_config=None):
        super().__init__(name, account_config, module_config)
        
        # 初始化HTTP客户端
        self.http_client = HTTPClient()
        
        # 注意：不要在这里定义指标，应在模块级别定义
        
    def collect(self):
        """
        收集ECS指标
        """
        try:
            # 使用HTTP客户端和指定的认证方式调用华为云API
            response = self.http_client.get(
                url=self.endpoint,
                auth_type=self.auth_type,
                ak=self.ak,
                sk=self.sk,
                iam_endpoint=self.iam_endpoint,
                domain_name=self.domain_name,
                username=self.username,
                password=self.password,
                project_id=self.project_id,
                region=self.region,
                service='ecs',
                params=self.params
            )
            
            data = response.json()
            
            # 解析响应数据并更新指标
            # ... 指标更新逻辑
            
        except Exception as e:
            logger.error(f"Error collecting ECS metrics for account {self.name}: {e}")
            
    def describe(self):
        """
        描述此收集器提供的指标
        """
        return [ECS_COUNT, ...]  # 返回所有指标对象
```

### 3.3 指标定义注意事项

1. **使用模块级变量**：避免在每次实例化时重复创建指标
2. **确保指标名称唯一**：在整个项目中不能有重复的指标名称
3. **合理设计标签**：标签应有助于多维度查询分析

``python
# 正确的指标定义方式
from prometheus_client import Gauge

# 模块级指标定义
ECS_COUNT = Gauge(
    'huaweicloud_ecs_total', 
    'Total number of ECS instances',
    ['account', 'region']
)

class EcsCollector(BaseCollector):
    def __init__(self, name, account_config, module_config=None):
        super().__init__(name, account_config, module_config)
        # 不要在这里重复定义指标
        
    def collect(self):
        # 使用模块级指标
        ECS_COUNT.labels(account=self.name, region=self.region).set(count)
```

### 3.4 错误处理最佳实践

1. 使用try-except捕获异常
2. 记录详细的错误信息
3. 确保程序在出错时仍能继续运行

``python
def collect(self):
    try:
        # API调用和数据处理逻辑
        pass
    except Exception as e:
        logger.error(f"Error collecting metrics for account {self.name}: {e}")
        # 不要重新抛出异常，确保不影响其他收集器
```

## 4. 配置文件设置

### 4.1 模块配置

在 `config/config.yaml` 中添加新模块配置：

```
modules:
  # 新增模块配置
  ecs:
    enabled: true                  # 是否启用该模块
    auth_type: "aksk"              # 认证方式: aksk 或 token
    project_id: "your-project-id"  # 项目ID
    region: "cn-north-1"           # 区域
    endpoint: "https://ecs.{project_id}.myhuaweicloud.com/v1"  # API端点
    collection_interval: "5m"      # 采集间隔
    params:                        # API请求参数
      limit: 100
```

### 4.2 认证配置

根据使用的认证方式，在账号或模块级别配置认证信息：

```
# AK/SK认证方式
auth:
  ak: "your-access-key"
  sk: "your-secret-key"

# Token认证方式
auth:
  domain_name: "your-domain-name"
  username: "your-username"
  password: "your-password"
  iam_endpoint: "https://iam.myhuaweicloud.com"
```

每个账号支持完整的认证配置，模块可以继承账号的认证信息或覆盖部分配置。

## 5. 自动注册机制

项目使用自动注册机制，无需手动添加引用：

1. 将采集器文件命名为 `<模块名>_metrics.py`
2. 类名应为 `<模块名首字母大写>Collector`
3. 在配置文件中启用模块

系统会自动导入并创建对应的收集器实例。

## 6. 测试与验证

### 6.1 启动测试

```
# 运行项目
python app.py

# 查看日志确认收集器是否成功创建
# 查看指标输出确认指标是否正确暴露
curl http://localhost:9091/metrics
```

### 6.2 指标验证

1. 确认指标名称符合规范
2. 确认标签设计合理
3. 确认指标值正确
4. 确认无重复注册错误

## 7. 注意事项

### 7.1 指标设计

1. **命名规范**：遵循 `huaweicloud_<服务名>_<指标名>` 格式
2. **标签设计**：包含丰富的标签以便多维度查询分析
3. **时间处理**：时间信息应转换为Unix时间戳
4. **状态处理**：状态码应标准化为0/1状态值
5. **单位处理**：测量单位ID应转换为可读的单位名称

### 7.2 数据处理

1. **None值处理**：确保所有传递给指标的值都不是None
2. **空数据处理**：在没有获取到数据时初始化相关指标值为0
3. **类型转换**：确保数值类型字段正确转换

### 7.3 错误处理

1. **异常捕获**：在收集器初始化和执行过程中增加完善的异常捕获机制
2. **日志记录**：增加详细的错误日志输出
3. **程序稳定性**：确保单个收集器出错不会影响整个项目运行

### 7.4 自监控指标

1. **Exporter会自动监控每个收集器的状态**：
   - `exporter_collector_up`指标会反映收集器是否正常工作
   - `exporter_collector_scrape_duration_seconds`指标会记录收集器执行时间
   - `exporter_scrape_errors_total`指标会统计错误次数

2. **收集器开发时应考虑**：
   - 不要让异常中断整个收集过程
   - 记录详细的错误日志以便问题排查
   - 对于部分API调用失败，应记录错误但继续执行其他操作

### 7.5 配置管理

1. **配置继承**：遵循项目的配置继承机制
2. **默认值保障**：为配置项提供默认值保障
3. **向后兼容**：确保现有配置文件兼容性

## 8. 文档更新

添加新采集器后，需要更新以下文档：

1. **README.md**：更新项目结构和收集器说明
2. **ARCHITECTURE.md**：更新架构设计和指标说明

## 9. 最佳实践总结

1. **设计一致性**：所有收集器遵循相同的配置结构
2. **灵活性**：为未来可能的扩展提供支持
3. **可维护性**：保持代码简洁和易于维护
4. **健壮性**：确保在各种异常情况下都能稳定运行

通过遵循以上指南，您可以成功地向华为云Exporter项目添加新的采集器，并确保其符合项目的整体设计和规范要求。

## 10. 示例：ShowCustomerAccountBalances收集器

以下是一个完整的示例，展示如何实现ShowCustomerAccountBalances API的收集器：

```
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

class SHOWCUSTOMERACCOUNTBALANCESCollector(BaseCollector):
    """
    ShowCustomerAccountBalances API指标收集器
    用于收集华为云账户余额信息
    专门使用AK/SK认证方式和华为云SDK
    """
    
    def __init__(self, name, account_config, module_config=None):
        super().__init__(name, account_config, module_config)
        
        # 初始化华为云BSS客户端
        try:
            # 使用配置中的AK/SK或者环境变量
            ak = self.ak or os.environ.get("CLOUD_SDK_AK")
            sk = self.sk or os.environ.get("CLOUD_SDK_SK")
            
            if not ak or not sk:
                logger.error(f"Missing AK/SK credentials for SHOWCUSTOMERACCOUNTBALANCES collector in account {self.name}")
                self.client = None
                return
                
            credentials = GlobalCredentials(ak, sk)
            
            # 使用配置中的区域或者默认区域
            region = self.region or "cn-north-1"
            
            self.client = BssClient.new_builder() \
                .with_credentials(credentials) \
                .with_region(BssRegion.value_of(region)) \
                .build()
                
        except Exception as e:
            logger.error(f"Failed to initialize BSS client for account {self.name}: {e}")
            self.client = None
    
    def collect(self):
        """
        收集ShowCustomerAccountBalances API指标
        """
        if not self.client:
            logger.warning(f"BSS client not initialized for SHOWCUSTOMERACCOUNTBALANCES collector in account {self.name}")
            return
            
        try:
            # 构造请求参数
            request = ShowCustomerAccountBalancesRequest()
            
            # 调用华为云API
            response = self.client.show_customer_account_balances(request)
            
            # 解析响应数据
            data = response.to_json_object()
            
            # 获取债务金额
            debt_amount = data.get('debt_amount', 0)
            currency = data.get('currency', 'CNY')
            
            # 更新总欠款金额指标
            DEBT_AMOUNT.labels(
                account=self.name,
                currency=currency
            ).set(debt_amount)
            
            # 解析账户余额列表数据并更新指标
            account_balances = data.get('account_balances', [])
            
            # 更新每个账户的详细指标
            for account in account_balances:
                account_id = account.get('account_id', 'unknown')
                account_type = self._get_account_type_name(account.get('account_type', 0))
                currency = account.get('currency', 'CNY')
                
                # 账户余额
                amount = account.get('amount', 0)
                ACCOUNT_BALANCE.labels(
                    account=self.name,
                    account_id=account_id,
                    account_type=account_type,
                    currency=currency
                ).set(amount)
                
        except exceptions.ClientRequestException as e:
            logger.error(f"Error collecting SHOWCUSTOMERACCOUNTBALANCES metrics for account {self.name}: "
                         f"status_code={e.status_code}, request_id={e.request_id}, "
                         f"error_code={e.error_code}, error_msg={e.error_msg}")
        except Exception as e:
            import traceback
            logger.error(f"Error collecting SHOWCUSTOMERACCOUNTBALANCES metrics for account {self.name}: {e}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            
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
        return type_map.get(account_type, f'unknown_type_{account_type}')
                
    def describe(self):
        """
        描述此收集器提供的指标
        """
        return [
            DEBT_AMOUNT,
            ACCOUNT_BALANCE
        ]
```

对应的配置文件示例：

```
modules:
  showcustomeraccountbalances:
    enabled: true                  # 是否启用该模块
    collection_interval: "1h"       # 采集间隔：支持多种单位（如：60s, 1m, 1h, 1d）
```

这个示例展示了如何使用华为云SDK实现一个基于AK/SK认证的收集器，以及如何处理API响应数据并转换为Prometheus指标。