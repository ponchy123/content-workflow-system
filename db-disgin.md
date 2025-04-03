1. 产品主表(products)
| 中文字段 | 英文字段 | 字段类型 | 备注 |
|---------|---------|---------|------|
| 产品ID | product_id | CHAR(12) | 主键 |
| 产品名称 | product_name | VARCHAR(100) | |
| 服务商 | provider_name | VARCHAR(100) | |
| 体积重系数 | dim_factor | DECIMAL(10,2) | |
| 体积重系数单位 | dim_factor_unit | VARCHAR(10) | 例如lb/in³ |
| 生效日期 | effective_date | DATE | |
| 失效日期 | expiration_date | DATE | |
| 国家 | country | VARCHAR(50) | |
| 币种 | currency | VARCHAR(3) | 例如USD |
| 描述 | description | TEXT | |
| 状态 | status | TINYINT(1) | 1=启用,0=禁用 |
| 启用开始日期 | enabled_start_date | DATE | |
| 启用结束日期 | enabled_end_date | DATE | |
2. 基础运费表(base_fees)
| 中文字段 | 英文字段 | 字段类型 | 备注 |
|---------|---------|---------|------|
| 费用ID | fee_id | INT | 主键，自增 |
| 产品ID | product_id | CHAR(12) | 外键，关联products表 |
| 重量 | weight | DECIMAL(10,3) | |
| 重量单位 | weight_unit | VARCHAR(5) | 例如OZ/LB/KG |
| 计费类型 | fee_type | VARCHAR(20) | STEP/LINEAR |
| Zone1基础价格 | zone1_price | DECIMAL(10,2) | |
| Zone2基础价格 | zone2_price | DECIMAL(10,2) | |
| Zone3基础价格 | zone3_price | DECIMAL(10,2) | |
| Zone4基础价格 | zone4_price | DECIMAL(10,2) | |
| Zone5基础价格 | zone5_price | DECIMAL(10,2) | |
| Zone6基础价格 | zone6_price | DECIMAL(10,2) | |
| Zone7基础价格 | zone7_price | DECIMAL(10,2) | |
| Zone8基础价格 | zone8_price | DECIMAL(10,2) | |
| Zone17基础价格 | zone17_price | DECIMAL(10,2) | |
| Zone1单位重量价格 | zone1_unit_price | DECIMAL(10,2) | |
| Zone2单位重量价格 | zone2_unit_price | DECIMAL(10,2) | |
| Zone3单位重量价格 | zone3_unit_price | DECIMAL(10,2) | |
| Zone4单位重量价格 | zone4_unit_price | DECIMAL(10,2) | |
| Zone5单位重量价格 | zone5_unit_price | DECIMAL(10,2) | |
| Zone6单位重量价格 | zone6_unit_price | DECIMAL(10,2) | |
| Zone7单位重量价格 | zone7_unit_price | DECIMAL(10,2) | |
| Zone8单位重量价格 | zone8_unit_price | DECIMAL(10,2) | |
| Zone17单位重量价格 | zone17_unit_price | DECIMAL(10,2) | |
3. 附加费表(surcharges)
| 中文字段 | 英文字段 | 字段类型 | 备注 |
|---------|---------|---------|------|
| 附加费ID | surcharge_id | INT | 主键，自增 |
| 产品ID | product_id | CHAR(12) | 外键，关联products表 |
| 附加费类型 | surcharge_type | VARCHAR(50) | |
| 子类型 | sub_type | VARCHAR(50) | |
| 条件描述 | condition_desc | TEXT | |
| Zone1附加费 | zone1_fee | DECIMAL(10,2) | |
| Zone2附加费 | zone2_fee | DECIMAL(10,2) | |
| Zone3附加费 | zone3_fee | DECIMAL(10,2) | |
| Zone4附加费 | zone4_fee | DECIMAL(10,2) | |
| Zone5附加费 | zone5_fee | DECIMAL(10,2) | |
| Zone6附加费 | zone6_fee | DECIMAL(10,2) | |
| Zone7附加费 | zone7_fee | DECIMAL(10,2) | |
| Zone8附加费 | zone8_fee | DECIMAL(10,2) | |
| Zone17附加费 | zone17_fee | DECIMAL(10,2) | |
4. 旺季附加费表(peak_season_surcharges)
| 中文字段 | 英文字段 | 字段类型 | 备注 |
|---------|---------|---------|------|
| 旺季附加费ID | pss_id | INT | 主键，自增 |
| 产品ID | product_id | CHAR(12) | 外键，关联products表 |
| 附加费类型 | surcharge_type | VARCHAR(50) | |
| 开始日期 | start_date | DATE | |
| 结束日期 | end_date | DATE | |
| 费用金额 | fee_amount | DECIMAL(10,2) |