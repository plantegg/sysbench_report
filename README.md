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
MYSQL_HOST=10.127.33.154      # MySQL服务器IP
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

**重要：在 MySQL 服务器上启动 tsar 监控**
```bash
# SSH 到 MySQL 服务器
ssh root@10.127.33.154

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

## 注意事项

1. **测试前必须启动 tsar**: 在 MySQL 服务器上手动启动 tsar 监控
2. **磁盘设备名**: 根据实际环境修改 tsar 命令中的磁盘设备名
3. **网络延迟**: 压测客户端与 MySQL 服务器网络延迟会影响结果
4. **数据准备**: 首次测试设置 `NEED_PREPARE=true`，后续可设为 `false`
5. **权限要求**: 需要 MySQL 服务器的 SSH root 权限用于监控数据采集

## 许可证

MIT License
