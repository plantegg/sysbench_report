# MySQL 性能压测工具

基于 sysbench + tsar 的 MySQL 性能压测和监控解决方案，支持自动化测试和完整的性能报告生成。

## 功能特性

- ✅ **完整性能测试**: 支持点查询、只读、读写混合、只写四种场景
- ✅ **系统监控**: 集成 tsar 监控，实时采集 CPU/IO 数据
- ✅ **时间精确匹配**: 监控数据与测试时间段精确对应
- ✅ **多格式报告**: 自动生成 HTML 和 Markdown 格式报告
- ✅ **灵活配置**: 支持自定义测试参数和场景

## 环境要求

### 压测客户端
- **操作系统**: Linux (CentOS/RHEL/AlmaLinux)
- **工具**: sysbench 1.0+, Python 3.6+
- **网络**: 到 MySQL 服务器的网络连接

### MySQL 服务器
- **监控工具**: tsar (用于 CPU/IO 监控)
- **权限**: SSH 免密登录访问
- **MySQL**: 5.7+ 或 8.0+

## 快速开始

### 1. 环境准备

**在压测客户端安装 sysbench:**
```bash
# CentOS/RHEL
yum install -y sysbench python3

# Ubuntu/Debian  
apt-get install -y sysbench python3
```

**在 MySQL 服务器安装 tsar:**
```bash
# 安装 tsar
yum install -y tsar
# 或从源码编译安装
```

### 2. 配置文件

编辑 `benchmark_config.conf`:
```bash
# 数据库配置
MYSQL_HOST=YOUR_MYSQL_HOST      # MySQL服务器IP
MYSQL_PORT=3316               # MySQL端口
MYSQL_USER=ren                # MySQL用户名
MYSQL_PASSWORD=your_password  # MySQL密码
MYSQL_DB=sbtest              # 测试数据库名

# 测试配置
TABLES=16                    # 测试表数量
TABLE_SIZE=100000           # 每表行数
TEST_TIME=10                # 每场景测试时间(秒)
NEED_PREPARE=true           # 是否重新准备数据

# 压测场景 (空格分隔)
SCENARIOS="oltp_point_select oltp_write_only"
# 可选: oltp_point_select oltp_read_only oltp_read_write oltp_write_only

# 并发线程数 (空格分隔)  
THREADS="1 128"
# 可选: 1 8 16 32 64 128
```

### 3. 测试前准备

**调整 max_prepared_stmt_count（必须在 prepare 之前）**

sysbench 在高并发（如 128 线程 × 16 表）时会创建大量 prepared statements，容易触发 MySQL 默认的 16382 上限导致报错：

```
FATAL: MySQL error: 1461 "Can't create more than max_prepared_stmt_count statements (current value: 16382)"
```

在执行 prepare 和 run 之前，先调大该参数：

```sql
-- 自建 MySQL：直接在线修改
SET GLOBAL max_prepared_stmt_count = 1048576;

-- 云托管服务（如 AWS Aurora、阿里云 RDS）：需要通过参数组/控制台修改后重启生效
-- Aurora: 创建自定义 DB Cluster Parameter Group，设置 max_prepared_stmt_count=1048576
-- 阿里云 RDS: 在控制台「参数设置」中修改
```

**重要：在 MySQL 服务器上启动 tsar 监控**
```bash
# SSH 到 MySQL 服务器
ssh root@YOUR_MYSQL_HOST

# 启动 tsar 监控 (替换 nvme1n1 为实际磁盘设备)
tsar --cpu --io -I nvme1n1 -l -i1 >/tmp/tsar.log 2>&1 &

# 确认 tsar 正在运行
ps aux | grep tsar
tail -f /tmp/tsar.log  # Ctrl+C 退出查看
```

**检查磁盘设备名称:**
```bash
lsblk | grep -E '(nvme|sda|vda)'  # 找到数据盘设备名
```

### 4. 执行测试

```bash
# 运行完整测试
./mysql_benchmark.sh benchmark_config.conf

# 自定义测试时间
./mysql_benchmark.sh benchmark_config.conf 30

# 使用现有数据(不重新准备)
./mysql_benchmark.sh benchmark_config.conf 10 false
```

### 5. 生成报告

测试完成后自动生成报告，也可手动生成:
```bash
# 生成 HTML 报告
python3 generate_report.py mysql_benchmark_YYYYMMDD_HHMMSS

# 生成 Markdown 报告  
python3 generate_markdown_report.py mysql_benchmark_YYYYMMDD_HHMMSS
```

### 7. 测试场景说明

使用 `merge_reports.py` 脚本可以将多个环境的测试报告合并成一个综合报告:

```bash
# 合并多个环境的报告
python3 merge_reports.py idc,idc.trx1,huawei,aliyun,aliyun.trx1

# 或者合并任意环境组合
python3 merge_reports.py env1,env2,env3
```

**脚本功能:**
- 自动读取各环境目录下的 `performance_report.md` 文件
- 生成性能对比摘要和结论分析
- 提取并转换 innodb_buffer_pool_size 为 GB 单位
- 创建统一的性能汇总表格(移除监控样本数列，添加环境标识)
- 按章节组织各环境的详细报告
- 在文档末尾统一放置监控数据说明和分析

**输出文件:** `mysql_sysbench.md` - 包含所有环境的综合性能测试报告

## 测试场景说明

| 场景 | 描述 | 主要指标 |
|------|------|----------|
| `oltp_point_select` | 主键点查询 | QPS, 延迟 |
| `oltp_read_only` | 只读事务 | TPS, QPS |
| `oltp_read_write` | 读写混合事务 | TPS, 延迟 |
| `oltp_write_only` | 只写事务 | TPS, IO利用率 |

## 报告内容

生成的报告包含:
- **性能指标**: QPS, TPS, 延迟分布
- **系统监控**: CPU利用率, IO利用率, 监控样本数
- **配置信息**: MySQL参数, 服务器配置, 测试参数
- **时间匹配**: 精确的测试时间段和监控数据对应

## 故障排除

### 常见问题

**1. tsar 监控数据为空**
```bash
# 检查 tsar 是否运行
ssh root@MYSQL_HOST "ps aux | grep tsar"

# 检查日志文件
ssh root@MYSQL_HOST "ls -la /tmp/tsar.log"

# 重启 tsar
ssh root@MYSQL_HOST "pkill tsar; tsar --cpu --io -I nvme1n1 -l -i1 >/tmp/tsar.log 2>&1 &"
```

**2. MySQL 连接失败**
```bash
# 测试连接
mysql -h MYSQL_HOST -P MYSQL_PORT -u MYSQL_USER -p

# 检查防火墙
telnet MYSQL_HOST MYSQL_PORT
```

**3. sysbench 命令不存在**
```bash
# 安装 sysbench
yum install -y sysbench
# 或
apt-get install -y sysbench
```

**4. 磁盘设备名错误**
```bash
# 查看所有磁盘设备
lsblk
df -h

# 更新配置中的设备名
# tsar --cpu --io -I 正确的设备名 -l -i1
```

### 性能调优建议

**MySQL 配置优化:**
```sql
-- 查看关键参数
SHOW VARIABLES WHERE Variable_name IN (
    'innodb_buffer_pool_size',
    'innodb_flush_log_at_trx_commit',
    'max_connections'
);

-- 建议配置
SET GLOBAL innodb_buffer_pool_size = '16G';  -- 70%内存
SET GLOBAL innodb_flush_log_at_trx_commit = 2;  -- 性能优化
```

**系统优化:**
```bash
# 检查 CPU 和内存
lscpu
free -h

# 检查磁盘 IO
iostat -x 1
```

## 项目结构

```
sysbench_report/
├── README.md                           # 项目文档
├── benchmark_config.conf               # 测试配置文件
├── mysql_benchmark.sh                  # 主测试脚本
├── generate_report.py                  # HTML报告生成器
├── generate_markdown_report.py         # Markdown报告生成器
├── merge_reports.py                    # 多环境报告合并脚本
└── final_mysql_benchmark_report/       # 示例测试结果
    ├── performance_report.html         # HTML格式报告
    ├── performance_report.md           # Markdown格式报告
    ├── tsar.log                       # 监控数据
    └── *.log                          # 测试日志
```

## 示例结果

基于 Intel Xeon 6982P-C (8核) + 30GB内存 + MySQL 5.7 的测试结果:

| 测试场景 | 1线程 | 128线程 | 性能提升 | CPU利用率 | IO利用率 |
|---------|-------|---------|----------|-----------|----------|
| **点查询** | 17,109 QPS | **321,410 QPS** | **18.9倍** | 12.9% | 0.1% |
| **只写** | 12,740 QPS | **139,564 QPS** | **10.9倍** | 6.4% | 52.3% |

## 压测 PaaS / 托管数据库（Aurora、RDS 等）

对于 AWS Aurora、阿里云 RDS、华为云 GaussDB 等 PaaS 类托管数据库服务，与自建 MySQL 压测有以下差异：

**无法 SSH 到数据库服务器**：托管服务不提供操作系统级访问，因此：
- 无法安装 tsar 采集 CPU/IO 指标
- 无法直接读取 MySQL 服务器的 lscpu、free 等信息
- 报告中 CPU/IO 监控列会显示 N/A

**替代监控方案**：
- AWS Aurora/RDS：使用 CloudWatch 指标（CPUUtilization、WriteIOPS、ReadIOPS、CommitLatency）
- 阿里云 RDS：使用云监控或 DAS 性能洞察
- 华为云：使用 Cloud Eye 监控

**参数修改方式不同**：
- `max_prepared_stmt_count` 等参数不能通过 `SET GLOBAL` 修改（权限不足）
- 需要通过云控制台的「参数组」功能修改，部分参数修改后需要重启实例生效

**使用方式**：
```bash
# 1. 配置文件中填写托管数据库的连接地址
MYSQL_HOST=your-instance.xxx.rds.amazonaws.com
MYSQL_PORT=3306
MYSQL_USER=admin
MYSQL_PASSWORD=your_password

# 2. 直接运行压测脚本（会跳过 SSH 相关步骤，tsar 数据为空属正常）
./mysql_benchmark.sh benchmark_config.conf

# 3. 生成的报告中 CPU/IO 列为 N/A，需结合云厂商监控面板查看
```

## 注意事项

1. **测试前必须启动 tsar**: 在 MySQL 服务器上手动启动 tsar 监控（仅自建环境）
2. **max_prepared_stmt_count**: 必须在 prepare 之前调大到 1048576，否则高并发会报错
3. **磁盘设备名**: 根据实际环境修改 tsar 命令中的磁盘设备名
4. **网络延迟**: 压测客户端与 MySQL 服务器网络延迟会影响结果，建议同 VPC/同机房
5. **数据准备**: 首次测试设置 `NEED_PREPARE=true`，后续可设为 `false`
6. **权限要求**: 自建环境需要 SSH root 权限；PaaS 环境无需 SSH，但需配置参数组

## 许可证

MIT License
