# 华为云Exporter指标文档

本文档详细列出了华为云Exporter暴露的所有Prometheus指标，按照收集器进行分类，并提供每个指标的描述、标签和使用方法。

## 目录

- [自监控指标](#自监控指标)
- [ListCertificates收集器](#listcertificates收集器)
- [ListFreeResourceInfos收集器](#listfreeresourceinfos收集器)
- [ListStoredValueCards收集器](#liststoredvaluecards收集器)
- [ShowCustomerAccountBalances收集器](#showcustomeraccountbalances收集器)
- [ListPayPerUseCustomerResources收集器](#listpayperusecustomerresources收集器)
- [ListCosts收集器](#listcosts收集器)
- [Domain收集器](#domain收集器)
- [Python运行时指标](#python运行时指标)

## 自监控指标

这些指标用于监控Exporter本身的运行状态。

### exporter_collector_up

指示每个收集器是否正常工作。

- **类型**: Gauge
- **标签**:
  - `collector`: 收集器名称
  - `account`: 账号名称
- **值**: 1表示正常，0表示异常
- **示例**:
  ```
  exporter_collector_up{account="hw057993413",collector="listcertificates"} 1.0
  exporter_collector_up{account="hw057993413",collector="listfreeresourceinfos"} 0.0
  ```

### exporter_collector_scrape_duration_seconds

记录每个收集器执行时间的直方图。

- **类型**: Histogram
- **标签**:
  - `collector`: 收集器名称
  - `account`: 账号名称
- **示例**:
  ```
  exporter_collector_scrape_duration_seconds_sum{account="hw057993413",collector="listcertificates"} 0.47456850000071427
  exporter_collector_scrape_duration_seconds_count{account="hw057993413",collector="listcertificates"} 1.0
  ```

### exporter_scrape_errors_total

统计抓取错误总数，按收集器、账号和错误类型分类。

- **类型**: Counter
- **标签**:
  - `collector`: 收集器名称
  - `account`: 账号名称
  - `error_type`: 错误类型 (import_error, unexpected_error, collection_error)
- **示例**:
  ```
  exporter_scrape_errors_total{account="hw057993413",collector="listcertificates",error_type="collection_error"} 1
  ```

## ListCertificates收集器

用于收集华为云账户中的SSL证书信息。

### huaweicloud_scm_certificate_total_count

账户中证书总数。

- **类型**: Gauge
- **标签**:
  - `account`: 账号名称
- **示例**:
  ```
  huaweicloud_scm_certificate_total_count{account="shihuahui"} 1.0
  ```

### huaweicloud_scm_certificate_status

证书状态，1表示ISSUED状态，0表示其他状态。

- **类型**: Gauge
- **标签**:
  - `account`: 账号名称
  - `certificate_id`: 证书ID
  - `domain`: 证书域名
- **示例**:
  ```
  huaweicloud_scm_certificate_status{account="shihuahui",certificate_id="scs1743384190324",domain="*.shihuahui-health.com"} 1.0
  ```

### huaweicloud_scm_certificate_expire_timestamp

证书过期时间戳。

- **类型**: Gauge
- **标签**:
  - `account`: 账号名称
  - `certificate_id`: 证书ID
  - `domain`: 证书域名
- **示例**:
  ```
  huaweicloud_scm_certificate_expire_timestamp{account="shihuahui",certificate_id="scs1743384190324",domain="*.shihuahui-health.com"} 1.775001599e+09
  ```

### huaweicloud_scm_certificate_info

证书详细信息。

- **类型**: Info
- **标签**:
  - `account`: 账号名称
  - `certificate_id`: 证书ID
  - `domain`: 证书域名
  - `name`: 证书名称
  - `sans`: 附加域名
  - `type`: 证书类型
  - `signature_algorithm`: 签名算法
  - `brand`: 证书品牌
  - `domain_type`: 域名类型
  - `validity_period`: 有效期(月)
  - `status`: 证书状态
  - `domain_count`: 域名数量
  - `wildcard_count`: 通配符域名数量
- **示例**:
  ```
  huaweicloud_scm_certificate_info{account="shihuahui",brand="GEOTRUST",certificate_id="scs1743384190324",domain="*.shihuahui-health.com",domain_count="1",domain_type="WILDCARD",name="scm-7b0cca",sans="shihuahui-health.com",signature_algorithm="SHA256withRSA",status="ISSUED",type="DV_SSL_CERT_BASIC",validity_period="12",wildcard_count="0"} 1.0
  ```

## ListFreeResourceInfos收集器

用于收集华为云账户中的免费资源包信息。

### huaweicloud_bss_free_resource_package_total_count

账户中免费资源包总数。

- **类型**: Gauge
- **标签**:
  - `account`: 账号名称
- **示例**:
  ```
  huaweicloud_bss_free_resource_package_total_count{account="hw057993413"} 16.0
  ```

### huaweicloud_bss_free_resource_package_status

免费资源包状态。

- **类型**: Gauge
- **标签**:
  - `account`: 账号名称
  - `order_instance_id`: 订单实例ID
  - `product_name`: 产品名称
  - `service_type_name`: 服务类型名称
- **值**:
  - 0: 未生效
  - 1: 生效中
  - 2: 已用完
  - 3: 已失效
  - 4: 已退订
- **示例**:
  ```
  huaweicloud_bss_free_resource_package_status{account="hw057993413",order_instance_id="01154-301381337-0",product_name="OBS公网流出流量包 100GB 包年",service_type_name="对象存储服务"} 0.0
  ```

### huaweicloud_bss_free_resource_amount

免费资源剩余额度。

- **类型**: Gauge
- **标签**:
  - `account`: 账号名称
  - `order_instance_id`: 订单实例ID
  - `product_name`: 产品名称
  - `usage_type_name`: 使用量类型名称
  - `measure_unit`: 度量单位
- **示例**:
  ```
  huaweicloud_bss_free_resource_amount{account="hw057993413",measure_unit="GB",order_instance_id="01154-301381337-0",product_name="OBS公网流出流量包 100GB 包年",usage_type_name="标准存储公网流出流量"} 100.0
  ```

### huaweicloud_bss_free_resource_original_amount

免费资源原始额度。

- **类型**: Gauge
- **标签**:
  - `account`: 账号名称
  - `order_instance_id`: 订单实例ID
  - `product_name`: 产品名称
  - `usage_type_name`: 使用量类型名称
  - `measure_unit`: 度量单位
- **示例**:
  ```
  huaweicloud_bss_free_resource_original_amount{account="hw057993413",measure_unit="GB",order_instance_id="01154-301381337-0",product_name="OBS公网流出流量包 100GB 包年",usage_type_name="标准存储公网流出流量"} 100.0
  ```

### huaweicloud_bss_free_resource_package_effective_timestamp

免费资源包生效时间戳。

- **类型**: Gauge
- **标签**:
  - `account`: 账号名称
  - `order_instance_id`: 订单实例ID
  - `product_name`: 产品名称
  - `service_type_name`: 服务类型名称
- **示例**:
  ```
  huaweicloud_bss_free_resource_package_effective_timestamp{account="hw057993413",order_instance_id="01154-301381337-0",product_name="OBS公网流出流量包 100GB 包年",service_type_name="对象存储服务"} 1.7574912e+09
  ```

### huaweicloud_bss_free_resource_package_expire_timestamp

免费资源包到期时间戳。

- **类型**: Gauge
- **标签**:
  - `account`: 账号名称
  - `order_instance_id`: 订单实例ID
  - `product_name`: 产品名称
  - `service_type_name`: 服务类型名称
- **示例**:
  ```
  huaweicloud_bss_free_resource_package_expire_timestamp{account="hw057993413",order_instance_id="01154-301381337-0",product_name="OBS公网流出流量包 100GB 包年",service_type_name="对象存储服务"} 1.789027199e+09
  ```

### huaweicloud_bss_free_resource_active_package_expire_timestamp

正在使用中的免费资源包到期时间戳。

- **类型**: Gauge
- **标签**:
  - `account`: 账号名称
  - `order_instance_id`: 订单实例ID
  - `product_name`: 产品名称
  - `service_type_name`: 服务类型名称
- **说明**: 该指标仅包含状态为"生效中"(status=1)的免费资源包的到期时间，用于跟踪当前正在使用的资源包何时到期
- **示例**:
  ```
  huaweicloud_bss_free_resource_active_package_expire_timestamp{account="hw057993413",order_instance_id="01154-301381337-0",product_name="OBS公网流出流量包 100GB 包年",service_type_name="对象存储服务"} 1.789027199e+09
  ```

### huaweicloud_bss_free_resource_package_info

免费资源包详细信息。

- **类型**: Info
- **标签**:
  - `account`: 账号名称
  - `order_instance_id`: 订单实例ID
  - `order_id`: 订单ID
  - `product_id`: 产品ID
  - `product_name`: 产品名称
  - `service_type_code`: 服务类型编码
  - `region_code`: 区域编码
  - `quota_reuse_mode`: 配额重用模式
  - `source_type`: 来源类型
  - `bundle_type`: 套餐类型
- **示例**:
  ```
  huaweicloud_bss_free_resource_package_info{account="hw057993413",bundle_type="ATOMIC_PKG",order_id="CS2507100925NO9PI",order_instance_id="01154-301381337-0",product_id="OFFI603857789081714713",product_name="OBS公网流出流量包 100GB 包年",quota_reuse_mode="1",region_code="cn-north-4",service_type_code="hws.service.type.obs",source_type="0"} 1.0
  ```

## ListStoredValueCards收集器

用于收集华为云账户中的储值卡信息。

### huaweicloud_bss_stored_value_card_total_count

账户中储值卡总数。

- **类型**: Gauge
- **标签**:
  - `account`: 账号名称
- **示例**:
  ```
  huaweicloud_bss_stored_value_card_total_count{account="hw057993413"} 1.0
  ```

### huaweicloud_bss_stored_value_card_status

储值卡状态。

- **类型**: Gauge
- **标签**:
  - `account`: 账号名称
  - `card_id`: 储值卡ID
  - `card_name`: 储值卡名称
- **值**:
  - 1: 可使用
  - 2: 已用完
- **示例**:
  ```
  huaweicloud_bss_stored_value_card_status{account="hw057993413",card_id="1129024999552458",card_name="华为云自定义面值储值卡"} 1.0
  ```

### huaweicloud_bss_stored_value_card_face_value

储值卡面值。

- **类型**: Gauge
- **标签**:
  - `account`: 账号名称
  - `card_id`: 储值卡ID
  - `card_name`: 储值卡名称
  - `currency`: 货币
- **示例**:
  ```
  huaweicloud_bss_stored_value_card_face_value{account="hw057993413",card_id="1129024999552458",card_name="华为云自定义面值储值卡",currency="CNY"} 154395.03
  ```

### huaweicloud_bss_stored_value_card_balance

储值卡余额。

- **类型**: Gauge
- **标签**:
  - `account`: 账号名称
  - `card_id`: 储值卡ID
  - `card_name`: 储值卡名称
  - `currency`: 货币
- **示例**:
  ```
  huaweicloud_bss_stored_value_card_balance{account="hw057993413",card_id="1129024999552458",card_name="华为云自定义面值储值卡",currency="CNY"} 20912.83
  ```

### huaweicloud_bss_stored_value_card_effective_timestamp

储值卡生效时间戳。

- **类型**: Gauge
- **标签**:
  - `account`: 账号名称
  - `card_id`: 储值卡ID
  - `card_name`: 储值卡名称
- **示例**:
  ```
  huaweicloud_bss_stored_value_card_effective_timestamp{account="hw057993413",card_id="1129024999552458",card_name="华为云自定义面值储值卡"} 1.669675725e+09
  ```

### huaweicloud_bss_stored_value_card_expire_timestamp

储值卡到期时间戳。

- **类型**: Gauge
- **标签**:
  - `account`: 账号名称
  - `card_id`: 储值卡ID
  - `card_name`: 储值卡名称
- **示例**:
  ```
  huaweicloud_bss_stored_value_card_expire_timestamp{account="hw057993413",card_id="1129024999552458",card_name="华为云自定义面值储值卡"} 1.764403199e+09
  ```

### huaweicloud_bss_stored_value_card_info

储值卡详细信息。

- **类型**: Info
- **标签**:
  - `account`: 账号名称
  - `card_id`: 储值卡ID
  - `card_name`: 储值卡名称
  - `face_value`: 面值
  - `balance`: 余额
  - `effective_time`: 生效时间
  - `expire_time`: 到期时间
  - `status`: 状态
- **示例**:
  ```
  huaweicloud_bss_stored_value_card_info{account="hw057993413",balance="20912.83",card_id="1129024999552458",card_name="华为云自定义面值储值卡",effective_time="2022-11-29T06:48:45Z",expire_time="2025-11-29T15:59:59Z",face_value="154395.03",status="1"} 1.0
  ```

## ShowCustomerAccountBalances收集器

用于收集华为云账户中的余额信息。

### huaweicloud_bss_debt_amount

账户总欠款金额。

- **类型**: Gauge
- **标签**:
  - `account`: 账号名称
  - `currency`: 货币
- **示例**:
  ```
  huaweicloud_bss_debt_amount{account="hw057993413",currency="CNY"} 0.0
  ```

### huaweicloud_bss_account_balance

账户余额。

- **类型**: Gauge
- **标签**:
  - `account`: 账号名称
  - `account_id`: 账户ID
  - `account_type`: 账户类型
  - `currency`: 货币
- **示例**:
  ```
  huaweicloud_bss_account_balance{account="hw057993413",account_id="AT0010183C5A4CC5F5",account_type="balance",currency="CNY"} 20.55
  ```

### huaweicloud_bss_account_designated_amount

账户专款专用余额。

- **类型**: Gauge
- **标签**:
  - `account`: 账号名称
  - `account_id`: 账户ID
  - `account_type`: 账户类型
  - `currency`: 货币
- **示例**:
  ```
  huaweicloud_bss_account_designated_amount{account="hw057993413",account_id="AT0010183C5A4CC5F5",account_type="balance",currency="CNY"} 0.0
  ```

### huaweicloud_bss_account_credit_amount

账户信用额度（仅信用账户存在该字段）。

- **类型**: Gauge
- **标签**:
  - `account`: 账号名称
  - `account_id`: 账户ID
  - `account_type`: 账户类型
  - `currency`: 货币
- **示例**:
  ```
  huaweicloud_bss_account_credit_amount{account="hw057993413",account_id="AT0010183C5A4CC5F5",account_type="balance",currency="CNY"} 0.0
  ```

### huaweicloud_bss_account_total_amount

账户总金额度（余额+专款专用余额+信用额度）。

- **类型**: Gauge
- **标签**:
  - `account`: 账号名称
  - `account_id`: 账户ID
  - `account_type`: 账户类型
  - `currency`: 货币
- **示例**:
  ```
  huaweicloud_bss_account_total_amount{account="hw057993413",account_id="AT0010183C5A4CC5F5",account_type="balance",currency="CNY"} 20.55
  ```

## ListPayPerUseCustomerResources收集器

用于收集华为云账户中的包年/包月资源信息。

### huaweicloud_bss_resource_total_count

账户中包年/包月资源总数。

- **类型**: Gauge
- **标签**:
  - `account`: 账号名称
- **示例**:
  ```
  huaweicloud_bss_resource_total_count{account="hw057993413"} 24.0
  ```

### huaweicloud_bss_resource_status

包年/包月资源状态。

- **类型**: Gauge
- **标签**:
  - `account`: 账号名称
  - `region`: 区域
  - `resource_id`: 资源ID
  - `resource_name`: 资源名称
  - `service_type_name`: 服务类型名称
  - `resource_type_name`: 资源类型名称
- **值**:
  - 1: 使用中
  - 0: 其他状态
- **示例**:
  ```
  huaweicloud_bss_resource_status{account="hw057993413",region="cn-north-4",resource_id="416604ed-dcf4-4094-b98f-ee149e5b1b72",resource_name="ecs-apps",resource_type_name="云主机",service_type_name="弹性云服务器"} 1.0
  ```

### huaweicloud_bss_resource_spec_size

包年/包月资源规格大小。

- **类型**: Gauge
- **标签**:
  - `account`: 账号名称
  - `region`: 区域
  - `resource_id`: 资源ID
  - `resource_name`: 资源名称
  - `service_type_name`: 服务类型名称
  - `resource_type_name`: 资源类型名称
  - `spec_unit`: 规格单位
- **示例**:
  ```
  huaweicloud_bss_resource_spec_size{account="hw057993413",region="cn-north-4",resource_id="0efbb5a0-cf90-4d42-8e33-4328b63b99bd",resource_name="SecMaster",resource_type_name="安全云脑-典型场景配置",service_type_name="安全云脑",spec_unit="unit_14"} 11.0
  ```

### huaweicloud_bss_resource_expire_timestamp

包年/包月资源到期时间戳。

- **类型**: Gauge
- **标签**:
  - `account`: 账号名称
  - `region`: 区域
  - `resource_id`: 资源ID
  - `resource_name`: 资源名称
  - `service_type_name`: 服务类型名称
  - `resource_type_name`: 资源类型名称
- **示例**:
  ```
  huaweicloud_bss_resource_expire_timestamp{account="hw057993413",region="cn-north-4",resource_id="416604ed-dcf4-4094-b98f-ee149e5b1b72",resource_name="ecs-apps",resource_type_name="云主机",service_type_name="弹性云服务器"} 1.763971199e+09
  ```

### huaweicloud_bss_resource_effective_timestamp

包年/包月资源生效时间戳。

- **类型**: Gauge
- **标签**:
  - `account`: 账号名称
  - `region`: 区域
  - `resource_id`: 资源ID
  - `resource_name`: 资源名称
  - `service_type_name`: 服务类型名称
  - `resource_type_name`: 资源类型名称
- **示例**:
  ```
  huaweicloud_bss_resource_effective_timestamp{account="hw057993413",region="cn-north-4",resource_id="416604ed-dcf4-4094-b98f-ee149e5b1b72",resource_name="ecs-apps",resource_type_name="云主机",service_type_name="弹性云服务器"} 1.669241907e+09
  ```

### huaweicloud_bss_resource_is_main

资源是否为主资源。

- **类型**: Gauge
- **标签**:
  - `account`: 账号名称
  - `region`: 区域
  - `resource_id`: 资源ID
  - `resource_name`: 资源名称
  - `service_type_name`: 服务类型名称
  - `resource_type_name`: 资源类型名称
- **值**:
  - 1: 主资源
  - 0: 附属资源
- **示例**:
  ```
  huaweicloud_bss_resource_is_main{account="hw057993413",region="cn-north-4",resource_id="416604ed-dcf4-4094-b98f-ee149e5b1b72",resource_name="ecs-apps",resource_type_name="云主机",service_type_name="弹性云服务器"} 1.0
  ```

### huaweicloud_bss_resource_info

包年/包月资源详细信息。

- **类型**: Info
- **标签**:
  - `account`: 账号名称
  - `region`: 区域
  - `resource_id`: 资源ID
  - `resource_name`: 资源名称
  - `service_type_name`: 服务类型名称
  - `resource_type_name`: 资源类型名称
  - `enterprise_project_id`: 企业项目ID
  - `enterprise_project_name`: 企业项目名称
  - `project_id`: 项目ID
  - `product_spec_desc`: 产品规格描述
  - `parent_resource_id`: 父资源ID
  - `id`: 资源实例ID
- **示例**:
  ```
  huaweicloud_bss_resource_info{account="hw057993413",enterprise_project_id="0",enterprise_project_name="default",id="01154-227980891-0",parent_resource_id="416604ed-dcf4-4094-b98f-ee149e5b1b72",product_spec_desc="通用计算增强型|ac7.large.2|2vCPUs|4GB|linux",project_id="404d7d518860467a8d9ec3f18ce3e02a",region="cn-north-4",resource_id="416604ed-dcf4-4094-b98f-ee149e5b1b72",resource_name="ecs-apps",resource_type_name="云主机",service_type_name="弹性云服务器"} 1.0
  ```

## ListCosts收集器

用于收集华为云账户中的成本信息。

### huaweicloud_bss_cost_amount

成本金额。

- **类型**: Gauge
- **标签**:
  - `account`: 账号名称
  - `time_dimension_value`: 时间维度值 (如2024-09)
  - `dimension_key`: 维度键 (如CHARGING_MODE)
  - `dimension_value`: 维度值 (如1表示包年/包月，3表示按需)
  - `amount_type`: 金额类型 (如net_amount表示净额)
- **示例**:
  ```
  huaweicloud_bss_cost_amount{account="hw057993413",amount_type="net_amount",dimension_key="CHARGING_MODE",dimension_value="1",time_dimension_value="2024-09"} 308.7
  ```

### huaweicloud_bss_official_cost_amount

官方成本金额。

- **类型**: Gauge
- **标签**:
  - `account`: 账号名称
  - `time_dimension_value`: 时间维度值 (如2024-09)
  - `dimension_key`: 维度键 (如CHARGING_MODE)
  - `dimension_value`: 维度值 (如1表示包年/包月，3表示按需)
- **示例**:
  ```
  huaweicloud_bss_official_cost_amount{account="hw057993413",dimension_key="CHARGING_MODE",dimension_value="1",time_dimension_value="2024-09"} 441.0
  ```

### huaweicloud_bss_cost_summary

成本汇总信息。

- **类型**: Gauge
- **标签**:
  - `account`: 账号名称
  - `dimension_key`: 维度键 (如CHARGING_MODE)
  - `dimension_value`: 维度值 (如1表示包年/包月，3表示按需)
  - `summary_type`: 汇总类型 (如net_amount表示净额，official_amount表示官方金额)
- **示例**:
  ```
  huaweicloud_bss_cost_summary{account="hw057993413",dimension_key="CHARGING_MODE",dimension_value="1",summary_type="net_amount"} 68772.32
  ```

## Domain收集器

用于收集华为云账户中的域名信息。

### huaweicloud_domain_total_count

账户中域名总数。

- **类型**: Gauge
- **标签**:
  - `account`: 账号名称
- **示例**:
  ```
  huaweicloud_domain_total_count{account="hw057993413"} 2.0
  ```

### huaweicloud_domain_status

域名状态。

- **类型**: Gauge
- **标签**:
  - `account`: 账号名称
  - `domain_name`: 域名
- **值**:
  - 1: 正常
  - 0: 异常
- **示例**:
  ```
  huaweicloud_domain_status{account="hw057993413",domain_name="byhuibao.com"} 0.0
  ```

### huaweicloud_domain_register_timestamp

域名注册时间戳。

- **类型**: Gauge
- **标签**:
  - `account`: 账号名称
  - `domain_name`: 域名
- **示例**:
  ```
  huaweicloud_domain_register_timestamp{account="hw057993413",domain_name="byhuibao.com"} 1.6697376e+09
  ```

### huaweicloud_domain_expire_timestamp

域名到期时间戳。

- **类型**: Gauge
- **标签**:
  - `account`: 账号名称
  - `domain_name`: 域名
- **示例**:
  ```
  huaweicloud_domain_expire_timestamp{account="hw057993413",domain_name="byhuibao.com"} 1.764432e+09
  ```

### huaweicloud_domain_info

域名详细信息。

- **类型**: Info
- **标签**:
  - `account`: 账号名称
  - `domain_name`: 域名
  - `order_id`: 订单ID
  - `audit_status`: 审核状态
  - `audit_fail_reason`: 审核失败原因
  - `reg_type`: 注册类型
  - `transfer_status`: 转移状态
- **示例**:
  ```
  huaweicloud_domain_info{account="hw057993413",audit_fail_reason="",audit_status="SUCCEED",domain_name="byhuibao.com",order_id="CS22113010020VWU5",reg_type="COMPANY",transfer_status=""} 1.0
  ```

### huaweicloud_domain_remaining_days

域名剩余天数。

- **类型**: Gauge
- **标签**:
  - `account`: 账号名称
  - `domain_name`: 域名
- **示例**:
  ```
  huaweicloud_domain_remaining_days{account="hw057993413",domain_name="byhuibao.com"} 85.0
  ```

### huaweicloud_domain_privacy_protection

域名是否启用隐私保护。

- **类型**: Gauge
- **标签**:
  - `account`: 账号名称
  - `domain_name`: 域名
- **值**:
  - 1: 启用
  - 0: 未启用
- **示例**:
  ```
  huaweicloud_domain_privacy_protection{account="hw057993413",domain_name="byhuibao.com"} 0.0
  ```

### huaweicloud_domain_auto_renew

域名是否自动续费。

- **类型**: Gauge
- **标签**:
  - `account`: 账号名称
  - `domain_name`: 域名
- **值**:
  - 1: 启用
  - 0: 未启用
- **示例**:
  ```
  huaweicloud_domain_auto_renew{account="hw057993413",domain_name="byhuibao.com"} 0.0
  ```

## Python运行时指标

这些是由Prometheus Python客户端库自动暴露的Python运行时指标。

### python_gc_objects_collected_total

垃圾回收期间收集的对象总数。

- **类型**: Counter
- **标签**:
  - `generation`: 代 (0, 1, 2)
- **示例**:
  ```
  python_gc_objects_collected_total{generation="0"} 279.0
  python_gc_objects_collected_total{generation="1"} 314.0
  python_gc_objects_collected_total{generation="2"} 0.0
  ```

### python_gc_objects_uncollectable_total

垃圾回收期间发现的无法回收的对象数量。

- **类型**: Counter
- **标签**:
  - `generation`: 代 (0, 1, 2)
- **示例**:
  ```
  python_gc_objects_uncollectable_total{generation="0"} 0.0
  python_gc_objects_uncollectable_total{generation="1"} 0.0
  python_gc_objects_uncollectable_total{generation="2"} 0.0
  ```

### python_gc_collections_total

各代垃圾回收执行的次数。

- **类型**: Counter
- **标签**:
  - `generation`: 代 (0, 1, 2)
- **示例**:
  ```
  python_gc_collections_total{generation="0"} 131.0
  python_gc_collections_total{generation="1"} 11.0
  python_gc_collections_total{generation="2"} 1.0
  ```

### python_info

Python解释器版本信息。

- **类型**: Gauge
- **标签**:
  - `implementation`: 实现 (如CPython)
  - `major`: 主版本号
  - `minor`: 次版本号
  - `patchlevel`: 补丁级别
  - `version`: 版本
- **示例**:
  ```
  python_info{implementation="CPython",major="3",minor="11",patchlevel="13",version="3.11.13"} 1.0
  ```