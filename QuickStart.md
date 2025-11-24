# MySQL 性能测试 QuickStart

## 环境要求

- **MySQL 服务器**：已安装 MySQL 5.7+ 或 8.0+/tsar
- **压测客户端**：已安装 sysbench 和 Python3

## 3 步开始测试

### 1. 下载脚本
```bash
下载本目录
```

### 2. 修改配置
编辑 `benchmark_config.conf`：
```bash
# 数据库配置
MYSQL_HOST=your_mysql_host     # 改为你的MySQL服务器IP
MYSQL_PORT=3306               # 改为你的MySQL端口
MYSQL_USER=root               # 改为你的MySQL用户名
MYSQL_PASSWORD=your_password  # 改为你的MySQL密码
```

运行tsar 按秒采集数据

```shell
#在被压的MySQL宿主机上执行（sfdv0n1 更换成你的 MySQL 所在的数据盘）：
nohup tsar --cpu --io -I sfdv0n1 -l -i1 >/tmp/tsar.log &
#修改被压 MySQL的参数：
set global max_prepared_stmt_count=1048576;
```

### 3. 运行测试

```bash
# 启动测试（自动生成报告）
./mysql_benchmark.sh benchmark_config.conf
```

## 测试结果

测试完成后自动生成：
- `mysql_benchmark_YYYYMMDD_HHMMSS/performance_report.html` - HTML报告
- `mysql_benchmark_YYYYMMDD_HHMMSS/performance_report.md` - Markdown报告

## 默认测试配置

- **测试场景**：点查询、只读、读写混合、只写
- **并发线程**：1, 8, 16, 32, 64, 128
- **数据规模**：16张表 × 1000万行
- **测试时间**：每场景30秒

## 自定义测试

```bash
# 启动测试
./mysql_benchmark.sh benchmark_config.conf

# 快速测试（10秒）
./mysql_benchmark.sh benchmark_config.conf 10

# 使用现有数据（不重新准备）
./mysql_benchmark.sh benchmark_config.conf 30 false
```

## 报告合并

如果对不同的参数/不同的机型分别进行了压测，想要对比的话，可以使用 `merge_reports.py` 合并多个环境的测试报告：

### 基本用法

```bash
# 合并多个环境的报告
python3 merge_reports.py idc,idc.trx1,huawei,aliyun,aliyun.trx1
```

### 目录结构要求

```
sysbench_report/
├── merge_reports.py
├── idc/
│   └── performance_report.md
├── idc.trx1/
│   └── performance_report.md
├── huawei/
│   └── performance_report.md
├── aliyun/
│   └── performance_report.md
└── aliyun.trx1/
    └── performance_report.md
```

### 生成的报告

- **mysql_sysbench.md** - 综合性能对比报告，包含：
  - 📊 环境配置对比表
  - 🏆 4种场景的性能对比（所有并发级别）
  - 📈 延迟分析表格
  - 💡 关键发现和建议

### 详细版报告

如果需要更详细的分析报告：

```bash
# 生成详细版报告
python3 merge_reports_v2.py idc,idc.trx1,huawei,aliyun,aliyun.trx1
```

生成 **mysql_sysbench_v2.md**，额外包含：
- 智能性能推荐
- 完整的性能扩展曲线
- 更详细的环境特点分析



## 故障排除

**连接失败**：
```bash
# 测试MySQL连接
mysql -h your_mysql_host -P 3306 -u root -p
```

**sysbench未安装**：
```bash
# CentOS/RHEL
yum install -y sysbench

# Ubuntu/Debian
apt-get install -y sysbench
```

**Python3未安装**：
```bash
# CentOS/RHEL
yum install -y python3

# Ubuntu/Debian
apt-get install -y python3
```

---
**就这么简单！** 🚀
