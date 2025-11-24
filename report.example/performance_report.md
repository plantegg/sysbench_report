# MySQL 性能测试报告 v7 Final

**测试时间**: 2025-11-23 19:09:42  
**测试工具**: sysbench + tsar (按时间段精确匹配)  
**tsar数据样本**: 1310 条记录  

## 测试配置信息

```
=== 测试配置信息 ===
MYSQL_HOST: 127.0.0.1
MYSQL_PORT: 3306
TABLES: 16
TABLE_SIZE: 1000000
TEST_TIME: 30

```

## MySQL配置参数

```
mysql: [Warning] Using a password on the command line interface can be insecure.
Variable_name	Value
innodb_buffer_pool_size	17179869184
innodb_flush_log_at_trx_commit	2

```

## 压测服务器配置

```
=== CPU 信息 ===
Architecture:          x86_64
CPU op-mode(s):        32-bit, 64-bit
Byte Order:            Little Endian
CPU(s):                48
On-line CPU(s) list:   0-47
Thread(s) per core:    2
Core(s) per socket:    12
座：                 2
NUMA 节点：         2
厂商 ID：           GenuineIntel
CPU 系列：          6
型号：              143
型号名称：        INTEL(R) XEON(R) SILVER 4510
步进：              8
CPU MHz：             2400.000
BogoMIPS：            4800.00
虚拟化：           VT-x
L1d 缓存：          48K
L1i 缓存：          32K
L2 缓存：           2048K
L3 缓存：           30720K
NUMA 节点0 CPU：    0,2,4,6,8,10,12,14,16,18,20,22,24,26,28,30,32,34,36,38,40,42,44,46
NUMA 节点1 CPU：    1,3,5,7,9,11,13,15,17,19,21,23,25,27,29,31,33,35,37,39,41,43,45,47
Flags:                 fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush dts acpi mmx fxsr sse sse2 ss ht tm pbe syscall nx pdpe1gb rdtscp lm constant_tsc art arch_perfmon pebs bts rep_good nopl xtopology nonstop_tsc aperfmperf eagerfpu pni pclmulqdq dtes64 monitor ds_cpl vmx smx est tm2 ssse3 sdbg fma cx16 xtpr pdcm pcid dca sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand lahf_lm abm 3dnowprefetch epb cat_l3 cat_l2 cdp_l3 invpcid_single intel_pt cdp_l2 ssbd mba ibrs ibpb stibp ibrs_enhanced tpr_shadow vnmi flexpriority ept vpid fsgsbase tsc_adjust bmi1 hle avx2 smep bmi2 erms invpcid rtm cqm rdt_a avx512f avx512dq rdseed adx smap avx512ifma clflushopt clwb avx512cd sha_ni avx512bw avx512vl xsaveopt xsavec xgetbv1 cqm_llc cqm_occup_llc cqm_mbm_total cqm_mbm_local dtherm ida arat pln pts avx512vbmi umip pku ospke avx512_vbmi2 gfni vaes vpclmulqdq avx512_vnni avx512_bitalg avx512_vpopcntdq cldemote movdiri movdir64b md_clear pconfig spec_ctrl intel_stibp flush_l1d arch_capabilities

=== 内存信息 ===
              total        used        free      shared  buff/cache   available
Mem:           376G         29G        342G        2.3G        4.6G        343G
Swap:            0B          0B          0B

```

## 性能测试结果汇总 (含CPU/IO监控数据)

| 测试场景 | 并发数 | QPS | TPS | 平均延迟(ms) | 95%延迟(ms) | CPU利用率(%) | CPU用户(%) | CPU系统(%) | CPU等待(%) | IO利用率(%) | 监控样本数 | 测试时间段 |
|---------|--------|-----|-----|-------------|-------------|-------------|------------|------------|------------|-------------|------------|------------|
| oltp_point_select | 1 | 33,572 | 33,572 | 0.03 | 0.03 | 0.0 | 0.7 | 0.5 | 0.0 | 0.0 | 31 | 2025-11-23 18:56:52 ~ 2025-11-23 18:57:22 |
| oltp_point_select | 8 | 186,824 | 186,824 | 0.04 | 0.05 | 0.3 | 4.9 | 3.2 | 0.0 | 0.0 | 31 | 2025-11-23 18:57:24 ~ 2025-11-23 18:57:54 |
| oltp_point_select | 16 | 269,096 | 269,096 | 0.06 | 0.09 | 0.7 | 7.9 | 4.7 | 0.0 | 0.0 | 31 | 2025-11-23 18:57:56 ~ 2025-11-23 18:58:26 |
| oltp_point_select | 32 | 318,015 | 318,015 | 0.10 | 0.16 | 0.8 | 10.3 | 5.9 | 0.0 | 0.0 | 31 | 2025-11-23 18:58:28 ~ 2025-11-23 18:58:58 |
| oltp_point_select | 64 | 307,471 | 307,471 | 0.21 | 0.28 | 0.8 | 10.4 | 5.8 | 0.0 | 0.0 | 31 | 2025-11-23 18:59:00 ~ 2025-11-23 18:59:30 |
| oltp_point_select | 128 | 289,999 | 289,999 | 0.44 | 0.58 | 0.9 | 10.5 | 5.7 | 0.0 | 0.0 | 31 | 2025-11-23 18:59:32 ~ 2025-11-23 19:00:02 |
| oltp_read_only | 1 | 12,542 | 784 | 1.28 | 1.32 | 0.0 | 1.4 | 0.3 | 0.0 | 0.0 | 31 | 2025-11-23 19:00:04 ~ 2025-11-23 19:00:34 |
| oltp_read_only | 8 | 55,531 | 3,471 | 2.30 | 3.55 | 0.2 | 8.8 | 1.0 | 0.0 | 0.0 | 31 | 2025-11-23 19:00:36 ~ 2025-11-23 19:01:06 |
| oltp_read_only | 16 | 72,489 | 4,531 | 3.53 | 5.47 | 0.2 | 13.4 | 1.5 | 0.0 | 0.0 | 31 | 2025-11-23 19:01:08 ~ 2025-11-23 19:01:38 |
| oltp_read_only | 32 | 76,153 | 4,760 | 6.72 | 9.39 | 0.2 | 14.7 | 1.6 | 0.0 | 0.0 | 31 | 2025-11-23 19:01:40 ~ 2025-11-23 19:02:10 |
| oltp_read_only | 64 | 75,745 | 4,734 | 13.52 | 17.01 | 0.3 | 14.7 | 1.7 | 0.0 | 0.0 | 31 | 2025-11-23 19:02:12 ~ 2025-11-23 19:02:42 |
| oltp_read_only | 128 | 74,513 | 4,657 | 27.48 | 31.94 | 0.3 | 14.6 | 1.7 | 0.0 | 0.0 | 31 | 2025-11-23 19:02:44 ~ 2025-11-23 19:03:14 |
| oltp_read_write | 1 | 11,375 | 569 | 1.76 | 1.89 | 0.0 | 1.6 | 0.5 | 0.0 | 2.1 | 31 | 2025-11-23 19:03:16 ~ 2025-11-23 19:03:46 |
| oltp_read_write | 8 | 58,118 | 2,906 | 2.75 | 3.96 | 0.2 | 10.3 | 1.7 | 0.0 | 3.0 | 32 | 2025-11-23 19:03:48 ~ 2025-11-23 19:04:19 |
| oltp_read_write | 16 | 69,645 | 3,482 | 4.59 | 7.43 | 0.2 | 13.4 | 1.9 | 0.0 | 3.5 | 31 | 2025-11-23 19:04:21 ~ 2025-11-23 19:04:51 |
| oltp_read_write | 32 | 71,619 | 3,581 | 8.93 | 13.95 | 0.3 | 14.1 | 2.0 | 0.0 | 3.8 | 31 | 2025-11-23 19:04:53 ~ 2025-11-23 19:05:23 |
| oltp_read_write | 64 | 72,613 | 3,631 | 17.62 | 32.53 | 0.3 | 14.2 | 1.9 | 0.0 | 3.8 | 31 | 2025-11-23 19:05:25 ~ 2025-11-23 19:05:55 |
| oltp_read_write | 128 | 72,912 | 3,646 | 35.09 | 75.82 | 0.3 | 14.3 | 1.9 | 0.0 | 3.5 | 31 | 2025-11-23 19:05:57 ~ 2025-11-23 19:06:27 |
| oltp_write_only | 1 | 20,554 | 3,426 | 0.29 | 0.38 | 0.0 | 1.9 | 1.0 | 0.0 | 3.5 | 31 | 2025-11-23 19:06:29 ~ 2025-11-23 19:06:59 |
| oltp_write_only | 8 | 84,693 | 14,115 | 0.57 | 0.83 | 0.3 | 9.2 | 3.0 | 0.1 | 9.1 | 31 | 2025-11-23 19:07:01 ~ 2025-11-23 19:07:31 |
| oltp_write_only | 16 | 104,302 | 17,384 | 0.92 | 1.52 | 0.4 | 11.2 | 3.3 | 0.0 | 10.1 | 31 | 2025-11-23 19:07:33 ~ 2025-11-23 19:08:03 |
| oltp_write_only | 32 | 114,258 | 19,043 | 1.68 | 3.19 | 0.4 | 11.8 | 3.1 | 0.0 | 10.9 | 31 | 2025-11-23 19:08:05 ~ 2025-11-23 19:08:35 |
| oltp_write_only | 64 | 116,587 | 19,431 | 3.29 | 7.43 | 0.5 | 12.0 | 3.0 | 0.0 | 9.3 | 31 | 2025-11-23 19:08:37 ~ 2025-11-23 19:09:07 |
| oltp_write_only | 128 | 127,103 | 21,184 | 6.04 | 14.21 | 0.5 | 12.3 | 3.2 | 0.0 | 8.7 | 31 | 2025-11-23 19:09:09 ~ 2025-11-23 19:09:39 |

### 监控数据说明

| 报告列名 | tsar对应列 | 说明 |
|---------|-----------|------|
| CPU利用率(%) | util | 总体CPU使用率 |
| CPU用户(%) | user | 用户态CPU使用率 |
| CPU系统(%) | sys | 内核态CPU使用率 |
| CPU等待(%) | wait | IO等待时间占用的CPU |
| IO利用率(%) | util (IO部分) | 磁盘IO使用率 |

## 测试结果分析

### 性能指标
- **QPS (Queries Per Second)**: 每秒查询数，衡量数据库处理查询的能力
- **TPS (Transactions Per Second)**: 每秒事务数，与QPS在点查询场景下相等
- **延迟 (Latency)**: 查询响应时间，包括平均延迟和95%分位延迟

### 系统监控指标
- **CPU利用率**: 总体CPU使用率
- **CPU用户**: 用户态CPU使用率
- **CPU系统**: 内核态CPU使用率  
- **CPU等待**: IO等待时间占用的CPU
- **IO利用率**: 磁盘IO使用率

### 关键发现
1. **性能扩展性**: 从低并发到高并发的性能扩展情况
2. **资源利用**: CPU和IO资源的使用效率
3. **延迟控制**: 高并发下的延迟表现
4. **瓶颈分析**: 系统瓶颈点识别

## 说明

- CPU/IO数据来源于tsar监控日志，按测试时间段精确匹配并计算平均值
- 监控样本数表示该测试时间段内tsar记录的数据点数量
- 系统监控数据与性能数据时间精确对应，确保数据准确性
- 测试使用sysbench工具，针对MySQL数据库进行标准化性能测试

---
*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
