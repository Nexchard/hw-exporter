# Huawei Cloud Prometheus Exporter

一个可扩展的Prometheus Exporter，用于从华为云服务收集监控指标。

## 功能特点

- 支持多个华为云账号的数据采集
- 模块化设计，易于扩展新的云服务指标采集器
- 可配置的采集频率和指标标签
- 支持热加载配置，无需重启即可应用配置更改
- 内置自监控指标，便于跟踪Exporter运行状态
- 支持模块级别的启用/禁用控制
- 支持每个模块独立配置project_id和region
- 支持多种认证方式（AK/SK认证和Token认证）
- 支持详细的日志调试信息，便于问题排查和监控

## 自监控指标

Exporter提供以下自监控指标，用于监控Exporter自身的运行状态：

- `exporter_collector_up`：收集器是否正常工作（1表示正常，0表示异常）
- `exporter_collector_scrape_duration_seconds`：收集器抓取耗时
- `exporter_scrape_errors_total`：抓取错误总数

## 指标说明

有关所有暴露指标的详细说明，请参阅 [METRICS.md](./docs/METRICS.md) 文件。

## 项目结构

```
huawei-cloud-exporter/
├── config/
│   └── config.yaml               # 主配置文件
├── collectors/                   # 采集器模块目录
│   ├── __init__.py
│   ├── base_collector.py         # 采集器基类，封装通用逻辑
│   ├── domain_metrics.py         # 域名信息采集器
│   ├── listfreeresourceinfos_metrics.py  # ListFreeResourceInfos API采集器
│   ├── liststoredvaluecards_metrics.py  # ListStoredValueCards API采集器
│   ├── showcustomeraccountbalances_metrics.py  # ShowCustomerAccountBalances API采集器
│   ├── listpayperusecustomerresources_metrics.py  # ListPayPerUseCustomerResources API采集器
│   ├── listcertificates_metrics.py  # ListCertificates API采集器
│   └── listcosts_metrics.py      # ListCosts API采集器
├── utils/
│   ├── auth.py                   # 华为云认证工具
│   └── http_client.py            # HTTP客户端工具
├── app.py                        # 主程序入口，启动HTTP服务器和调度采集任务
├── pyproject.toml                # 项目配置和依赖管理文件
├── docs/                         # 文档目录
│   ├── COLLECTOR_DEVELOPMENT_GUIDE.md # 采集器开发指南
│   ├── METRICS.md                 # 指标说明文档
│   └── ARCHITECTURE.md            # 架构设计文档
└── README.md                     # 项目说明文档
```

## 配置说明

配置文件支持多个华为云账号的配置，每个账号可以设置不同的认证信息和多个监控模块。每个模块可以独立配置：
- 是否启用(enabled)
- 认证方式(auth_type): aksk 或 token
- 采集间隔(collection_interval)
- 自定义参数(params)

对于AK/SK认证方式，需要提供:
- ak: Access Key ID
- sk: Secret Access Key

对于Token认证方式，需要提供:
- domain_name: IAM用户所属账号名
- username: IAM用户名
- password: IAM用户密码
- iam_endpoint: IAM端点

### 配置继承机制

配置采用继承机制，模块级别的配置会优先使用模块自身配置，如果没有配置则会继承账号级别的配置：
- 认证信息（ak, sk, domain_name, username, password, iam_endpoint等）
- 项目和区域信息（project_id, region）
- 其他通用配置

这样可以避免重复配置，提高配置文件的简洁性和可维护性。

## 数据采集机制

Exporter采用主动采集模式，定期请求华为云API获取数据并存储在内存中。当Prometheus请求/metrics端点时，直接返回已采集的数据，不会在收到请求时再去请求华为云API。

采集间隔由配置文件中各模块的`collection_interval`参数决定。系统会使用所有启用模块中最小的`collection_interval`值作为实际的采集间隔。

### collection_interval配置说明

`collection_interval`参数支持多种配置方式：

1. **纯数字**：表示秒数
   - `collection_interval: 60` 表示60秒

2. **带单位的字符串**：支持以下单位
   - 秒：`s`, `sec`, `second`, `seconds`
   - 分钟：`m`, `min`, `minute`, `minutes`
   - 小时：`h`, `hr`, `hour`, `hours`
   - 天：`d`, `day`, `days`

   示例：
   - `collection_interval: "1m"` 表示1分钟
   - `collection_interval: "1h"` 表示1小时
   - `collection_interval: "1d"` 表示1天

## 日志调试功能

为了便于调试和监控，项目支持详细的日志输出功能。日志级别可以通过配置文件进行配置：

```yaml
exporter:
  # Exporter监听端口
  port: 9091
  # Exporter监听地址
  address: "0.0.0.0"
  # 日志级别 (可选: DEBUG, INFO, WARNING, ERROR, CRITICAL)
  log_level: "INFO"
```

日志级别说明：
- `DEBUG`: 最详细的日志信息，包括参数处理、中间计算结果、API调用细节等
- `INFO`: 一般信息性日志，显示程序运行过程和重要事件
- `WARNING`: 警告信息，表示可能有问题但不影响程序运行
- `ERROR`: 错误信息，表示发生了错误但程序可以继续运行
- `CRITICAL`: 严重错误信息，可能导致程序无法继续运行

在开发和调试阶段，建议将日志级别设置为`DEBUG`以获取最详细的信息。在生产环境中，建议使用`INFO`或`WARNING`级别以减少日志输出量。

## 收集器说明

### ListFreeResourceInfos收集器 (listfreeresourceinfos_metrics.py)

用于收集华为云账户中的免费资源包信息，专门使用AK/SK认证方式和华为云SDK，提供了以下指标：

- `huaweicloud_bss_free_resource_package_total_count`：账户中免费资源包总数
- `huaweicloud_bss_free_resource_package_status`：免费资源包状态 (0:未生效, 1:生效中, 2:已用完, 3:已失效, 4:已退订)
- `huaweicloud_bss_free_resource_amount`：免费资源剩余额度
- `huaweicloud_bss_free_resource_original_amount`：免费资源原始额度
- `huaweicloud_bss_free_resource_package_effective_timestamp`：免费资源包生效时间戳
- `huaweicloud_bss_free_resource_package_expire_timestamp`：免费资源包到期时间戳
- `huaweicloud_bss_free_resource_package_info`：免费资源包详细信息（Info类型指标）

该收集器支持以下API请求参数配置：
- `region_code`: 云服务区编码
- `order_id`: 订单ID
- `product_id`: 产品ID，即资源包ID
- `product_name`: 产品名称，即资源包名称
- `enterprise_project_id`: 企业项目ID
- `status`: 状态 (0:未生效, 1:生效中, 2:已用完, 3:已失效, 4:已退订)
- `offset`: 偏移量，默认为0
- `limit`: 每次查询的记录数，默认为10
- `service_type_code_list`: 云服务类型编码列表

### ListStoredValueCards收集器 (liststoredvaluecards_metrics.py)

用于收集华为云账户中的储值卡信息，专门使用AK/SK认证方式和华为云SDK，提供了以下指标：

- `huaweicloud_bss_stored_value_card_total_count`：账户中储值卡总数
- `huaweicloud_bss_stored_value_card_status`：储值卡状态 (1表示可使用，2表示已用完)
- `huaweicloud_bss_stored_value_card_face_value`：储值卡面值
- `huaweicloud_bss_stored_value_card_balance`：储值卡余额
- `huaweicloud_bss_stored_value_card_effective_timestamp`：储值卡生效时间戳
- `huaweicloud_bss_stored_value_card_expire_timestamp`：储值卡到期时间戳
- `huaweicloud_bss_stored_value_card_info`：储值卡详细信息（Info类型指标）

该收集器支持以下API请求参数配置：
- `status`: 储值卡状态，1表示可使用，2表示已用完
- `card_id`: 储值卡ID
- `offset`: 偏移量，默认值为0
- `limit`: 查询的储值卡数量，默认值为10

### ShowCustomerAccountBalances收集器 (showcustomeraccountbalances_metrics.py)

用于收集华为云账户中的余额信息，专门使用AK/SK认证方式和华为云SDK，提供了以下指标：

- `huaweicloud_bss_debt_amount`：账户总欠款金额
- `huaweicloud_bss_account_balance`：账户余额
- `huaweicloud_bss_account_designated_amount`：账户专款专用余额
- `huaweicloud_bss_account_credit_amount`：账户信用额度（仅信用账户存在该字段）
- `huaweicloud_bss_account_total_amount`：账户总金额度（余额+专款专用余额+信用额度）

该收集器不需要API请求参数。

### ListPayPerUseCustomerResources收集器 (listpayperusecustomerresources_metrics.py)

用于收集华为云账户中的包年/包月资源信息，专门使用AK/SK认证方式和华为云SDK，提供了以下指标：

- `huaweicloud_bss_resource_total_count`：账户中包年/包月资源总数
- `huaweicloud_bss_resource_status`：包年/包月资源状态 (1表示使用中，0表示其他状态)
- `huaweicloud_bss_resource_spec_size`：包年/包月资源规格大小
- `huaweicloud_bss_resource_expire_timestamp`：包年/包月资源到期时间戳
- `huaweicloud_bss_resource_effective_timestamp`：包年/包月资源生效时间戳
- `huaweicloud_bss_resource_is_main`：资源是否为主资源 (1表示主资源，0表示附属资源)
- `huaweicloud_bss_resource_info`：包年/包月资源详细信息（Info类型指标）

该收集器支持以下API请求参数配置：
- `status_list`: 资源状态列表，例如 [2] 表示查询使用中的资源
- `only_main_resource`: 是否只查询主资源，1表示只查询主资源，0表示查询主资源及附属资源
- `limit`: 每次查询的条数，范围1-500

### ListCosts收集器 (listcosts_metrics.py)

用于收集华为云账户中的成本信息，专门使用AK/SK认证方式和华为云SDK，提供了以下指标：

- `huaweicloud_bss_cost_amount`：成本金额
- `huaweicloud_bss_official_cost_amount`：官方成本金额
- `huaweicloud_bss_cost_summary`：成本汇总信息

该收集器支持以下API请求参数配置：
- `begin_time`: 开始时间，格式为YYYY-MM，如果不配置则自动计算为当前月份往前12个月
- `end_time`: 结束时间，格式为YYYY-MM，如果不配置则自动计算为当前月份
- `amount_type`: 金额类型（NET_AMOUNT:净额, TAX_AMOUNT:税额, TOTAL_AMOUNT:总额）
- `cost_type`: 成本类型（ORIGINAL_COST:原始成本, DISCOUNT_COST:折扣成本, REFUND_COST:退款成本）
- `groupby`: 分组条件，按维度分组（如CHARGING_MODE:计费模式）
- `filters`: 过滤条件

### 域名收集器 (domain_metrics.py)

用于收集华为云账户中的域名信息，使用Token认证方式，提供了以下指标：

- `huaweicloud_domain_total_count`：账户中域名总数
- `huaweicloud_domain_status`：域名状态 (1表示正常，0表示异常)
- `huaweicloud_domain_register_timestamp`：域名注册时间戳
- `huaweicloud_domain_expire_timestamp`：域名到期时间戳
- `huaweicloud_domain_info`：域名详细信息（Info类型指标）
- `huaweicloud_domain_remaining_days`：域名剩余天数
- `huaweicloud_domain_privacy_protection`：域名是否启用隐私保护 (1表示启用，0表示未启用)
- `huaweicloud_domain_auto_renew`：域名是否自动续费 (1表示启用，0表示未启用)

### ListCertificates收集器 (listcertificates_metrics.py)

用于收集华为云账户中的SSL证书信息，专门使用AK/SK认证方式和华为云SDK，提供了以下指标：

- `huaweicloud_scm_certificate_total_count`：账户中证书总数
- `huaweicloud_scm_certificate_status`：证书状态 (1表示ISSUED状态，0表示其他状态)
- `huaweicloud_scm_certificate_expire_timestamp`：证书过期时间戳
- `huaweicloud_scm_certificate_info`：证书详细信息（Info类型指标）

该收集器支持以下API请求参数配置：
- `limit`: 每页条目数量，取值：10/20/50
- `offset`: 偏移量
- `sort_dir`: 排序方式，取值：ASC/DESC
- `sort_key`: 排序依据参数，取值：certExpiredTime/certStatus/certUpdateTime
- `status`: 证书状态，取值：ALL/PAID/ISSUED等
- `enterprise_project_id`: 企业多项目ID
- `deploy_support`: 是否仅筛选支持部署的证书
- `owned_by_self`: 过滤资源是否属于当前租户
- `expired_days_since`: 证书在有效期内及最多过期xx天


## 配置文件示例

```
# 华为云Exporter配置文件

exporter:
  # Exporter监听端口
  port: 9091
  # Exporter监听地址
  address: "0.0.0.0"
  
# 多账号配置
# 注意：请将下面的认证信息替换为您从华为云获取的真实凭证
# 获取方式：登录华为云控制台 -> 我的凭证 -> 访问密钥 -> 新增访问密钥
huawei_cloud_accounts:
  - name: "account1"
    auth:
      # AK/SK认证方式所需信息
      ak: "your_access_key_1"      # 替换为您的Access Key
      sk: "your_secret_key_1"      # 替换为您的Secret Key
      # Token认证方式所需信息
      domain_name: "your_domain_name_1"  # IAM用户所属账号名
      username: "your_username_1"         # IAM用户名
      password: "your_password_1"        # IAM用户密码
      # IAM端点，用于获取Token
      iam_endpoint: "https://iam.myhuaweicloud.com"
    modules:
      # ListCertificates API模块配置 - 证书查询
      listcertificates:
        enabled: true                  # 是否启用该模块
        collection_interval: "1h"       # 采集间隔：支持多种单位（如：60s, 1m, 1h, 1d）

      # ListFreeResourceInfos API模块配置 - 免费资源包查询
      listfreeresourceinfos:
        enabled: true                  # 是否启用该模块
        # 该模块专门使用AK/SK认证方式，不需要配置endpoint
        collection_interval: "1h"       # 采集间隔：支持多种单位（如：60s, 1m, 1h, 1d）
      
      # ListStoredValueCards API模块配置 - 储值卡查询
      liststoredvaluecards:
        enabled: true                  # 是否启用该模块
        # 该模块专门使用AK/SK认证方式，不需要配置endpoint
        collection_interval: "1h"       # 采集间隔：支持多种单位（如：60s, 1m, 1h, 1d）
        params:                        # API请求参数
          status: 1                    # 只查询可使用的储值卡
      
      # ShowCustomerAccountBalances API模块配置 - 账户余额查询
      showcustomeraccountbalances:
        enabled: true                  # 是否启用该模块
        # 该模块专门使用AK/SK认证方式，不需要配置endpoint
        collection_interval: "1h"       # 采集间隔：支持多种单位（如：60s, 1m, 1h, 1d）
        
      # ListPayPerUseCustomerResources API模块配置 - 包年/包月资源查询
      listpayperusecustomerresources:
        enabled: true                  # 是否启用该模块
        # 该模块专门使用AK/SK认证方式，不需要配置endpoint
        collection_interval: "1h"       # 采集间隔：支持多种单位（如：60s, 1m, 1h, 1d）
        params:                        # API请求参数
          status_list: [2]             # 资源状态：2表示使用中的资源
          only_main_resource: 1        # 只查询主资源
          limit: 500                   # 每次查询的条数
          
      # ListCosts API模块配置 - 成本查询
      listcosts:
        enabled: true                  # 是否启用该模块
        # 该模块专门使用AK/SK认证方式，不需要配置endpoint
        collection_interval: "1d"       # 采集间隔：支持多种单位（如：60s, 1m, 1h, 1d）
        params:                        # API请求参数
          # begin_time: "2024-08"      # 开始时间，格式为YYYY-MM，如果不配置则自动计算为当前月份往前12个月
          # end_time: "2025-08"        # 结束时间，格式为YYYY-MM，如果不配置则自动计算为当前月份
          # amount_type: "NET_AMOUNT"  # 金额类型：NET_AMOUNT（净额）, TAX_AMOUNT（税额）, TOTAL_AMOUNT（总额）
          # cost_type: "ORIGINAL_COST" # 成本类型：ORIGINAL_COST（原始成本）, DISCOUNT_COST（折扣成本）, REFUND_COST（退款成本）
          # groupby:                   # 分组条件，按维度分组
          #   - type: "dimension"
          #     key: "CHARGING_MODE"   # 可选值：CHARGING_MODE（计费模式）, RESOURCE_TYPE 等
          # filters: []                # 过滤条件，默认为空

      # 域名信息收集器模块配置
      domain:
        enabled: true                  # 是否启用该模块
        auth_type: "token"             # 认证方式: aksk 或 token
        # 认证信息将从账号配置继承
        # domain_name, username, password 将使用账号级别的配置
        # iam_endpoint 将使用账号级别的配置
        # endpoint 可选配置，如不配置将使用默认值 https://domain.myhuaweicloud.com
        collection_interval: "1h"       # 采集间隔：1小时
        params:                        # API请求参数
          limit: 200                   # 每次查询的条数

        
  - name: "account2"
    auth:
      # AK/SK认证方式所需信息
      ak: "your_access_key_2"      # 替换为您的Access Key
      sk: "your_secret_key_2"      # 替换为您的Secret Key
      # Token认证方式所需信息
      domain_name: "your_domain_name_2"  # IAM用户所属账号名
      username: "your_username_2"         # IAM用户名
      password: "your_password_2"        # IAM用户密码
      # IAM端点，用于获取Token
      iam_endpoint: "https://iam.myhuaweicloud.com"
    modules:
      # ListCertificates API模块配置 - 证书查询
      listcertificates:
        enabled: true                  # 是否启用该模块
        collection_interval: "1h"       # 采集间隔：支持多种单位（如：60s, 1m, 1h, 1d）

      # ListFreeResourceInfos API模块配置 - 免费资源包查询
      listfreeresourceinfos:
        enabled: true                 # 是否启用该模块
        # 该模块专门使用AK/SK认证方式，不需要配置endpoint
        collection_interval: "1h"      # 采集间隔：1小时
      
      # ListStoredValueCards API模块配置 - 储值卡查询
      liststoredvaluecards:
        enabled: true                 # 是否启用该模块
        # 该模块专门使用AK/SK认证方式，不需要配置endpoint
        collection_interval: "1h"      # 采集间隔：1小时
        params:                       # API请求参数
          status: 1                   # 只查询可使用的储值卡
      
      # ShowCustomerAccountBalances API模块配置 - 账户余额查询
      showcustomeraccountbalances:
        enabled: true                 # 是否启用该模块
        # 该模块专门使用AK/SK认证方式，不需要配置endpoint
        collection_interval: "1h"      # 采集间隔：1小时
        
      # ListPayPerUseCustomerResources API模块配置 - 包年/包月资源查询
      listpayperusecustomerresources:
        enabled: true                 # 是否启用该模块
        # 该模块专门使用AK/SK认证方式，不需要配置endpoint
        collection_interval: "1h"      # 采集间隔：1小时
        params:                        # API请求参数
          status_list: [2]             # 资源状态：2表示使用中的资源
          only_main_resource: 1        # 只查询主资源
          limit: 500                   # 每次查询的条数

      # ListCosts API模块配置 - 成本查询
      listcosts:
        enabled: true                  # 是否启用该模块
        # 该模块专门使用AK/SK认证方式，不需要配置endpoint
        collection_interval: "1d"       # 采集间隔：支持多种单位（如：60s, 1m, 1h, 1d）
        params:                        # API请求参数
          # begin_time: "2024-08"      # 开始时间，格式为YYYY-MM，如果不配置则自动计算为当前月份往前12个月
          # end_time: "2025-08"        # 结束时间，格式为YYYY-MM，如果不配置则自动计算为当前月份
          # amount_type: "NET_AMOUNT"  # 金额类型：NET_AMOUNT（净额）, TAX_AMOUNT（税额）, TOTAL_AMOUNT（总额）
          # cost_type: "ORIGINAL_COST" # 成本类型：ORIGINAL_COST（原始成本）, DISCOUNT_COST（折扣成本）, REFUND_COST（退款成本）
          # groupby:                   # 分组条件，按维度分组
          #   - type: "dimension"
          #     key: "CHARGING_MODE"   # 可选值：CHARGING_MODE（计费模式）, RESOURCE_TYPE 等
          # filters: []                # 过滤条件，默认为空
          
      # 域名信息收集器模块配置
      domain:
        enabled: true                 # 是否启用该模块
        auth_type: "token"             # 认证方式: aksk 或 token
        # 认证信息将从账号配置继承
        collection_interval: "1h"       # 采集间隔：1小时
        params:                        # API请求参数
          limit: 200                   # 每次查询的条数
```

## 指标查询示例

可以通过Prometheus查询语言(PromQL)查询指标：

1. 查询账户免费资源包总数：
```
huaweicloud_bss_free_resource_package_total_count{account="account1"}
```

2. 查询特定免费资源包的状态：
```
huaweicloud_bss_free_resource_package_status{product_name="OBS公网流出流量包 100GB 包年"}
```

3. 查询免费资源剩余额度：
```
huaweicloud_bss_free_resource_amount
```

4. 查询储值卡余额：
```
huaweicloud_bss_stored_value_card_balance{account="account1"}
```

5. 查询包年包月资源总数：
```
huaweicloud_bss_resource_total_count
```

## 故障排除

如果遇到问题，请检查以下几点：

1. 确保配置文件中的认证信息正确无误
2. 确认网络连接正常，可以访问华为云API
3. 检查日志输出，查看是否有错误信息
4. 确认配置的AK/SK具有相应的API访问权限

## 部署教程

### 系统要求

- Rocky Linux 9 或兼容的EL9系统
- Python 3.8 或更高版本
- systemd (用于服务管理)

### 安装步骤

1. **安装uv工具**
   ```bash
   # 使用官方脚本安装uv（推荐）
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **安装Python**
   ```bash
   # 使用uv安装Python（推荐方式）
   uv python install 3.11
   ```

3. **获取项目文件**
   ```bash
   # 克隆项目仓库
   git clone https://github.com/Nexchard/hw-exporter.git /opt/hw-exporter
   
   # 切换到项目目录
   cd /opt/hw-exporter
   
   # 安装项目依赖
   uv sync
   ```
   
5. **配置服务**
   ```bash
   # 复制服务文件
   cp /opt/hw-exporter/hw-exporter.service /etc/systemd/system/
   
   # 重新加载systemd配置
   systemctl daemon-reload
   
   # 启用服务
   systemctl enable hw-exporter
   ```

6. **配置华为云认证信息**
   ```bash
   # 编辑配置文件
   vim /opt/hw-exporter/config/config.yaml
   
   # 根据需要填写华为云AK/SK或用户名密码等认证信息
   ```

7. **启动服务**
   ```bash
   # 启动服务
   systemctl start hw-exporter
   
   # 检查服务状态
   systemctl status hw-exporter
   
   # 查看日志
   journalctl -u hw-exporter -f
   ```

### 验证部署

启动服务后，可以通过以下方式验证部署是否成功：

1. **检查服务状态**
   ```bash
   systemctl status hw-exporter
   ```

2. **检查监听端口**
   ```bash
   netstat -tlnp | grep 9091
   ```

3. **查看指标**
   ```bash
   curl http://localhost:9091/metrics
   ```

### 更新项目

要更新项目到最新版本：

1. **停止服务**
   ```bash
   systemctl stop hw-exporter
   ```

2. **备份配置文件**
   ```bash
   cp /opt/hw-exporter/config/config.yaml /opt/hw-exporter/config/config.yaml.backup
   ```

3. **更新代码**
   ```bash
   # 进入项目目录
   cd /opt/hw-exporter
   
   # 拉取最新代码
   git pull
   ```

4. **更新依赖**
   ```bash
   # 切换到项目目录
   cd /opt/hw-exporter
   
   # 使用uv更新依赖
   uv sync
   ```

5. **恢复配置文件**
   ```bash
   cp /opt/hw-exporter/config/config.yaml.backup /opt/hw-exporter/config/config.yaml
   ```

6. **启动服务**
   ```bash
   systemctl start hw-exporter
   ```

## 贡献

欢迎提交Issue和Pull Request来改进这个项目。

## 许可证

本项目采用MIT许可证。