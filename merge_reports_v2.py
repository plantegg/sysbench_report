#!/usr/bin/env python3
import sys
import os
import re
from datetime import datetime

def extract_innodb_buffer_pool_size(content):
    """Extract and convert innodb_buffer_pool_size to GB"""
    match = re.search(r'innodb_buffer_pool_size\s+(\d+)', content)
    if match:
        bytes_size = int(match.group(1))
        gb_size = bytes_size / (1024**3)
        return f"{gb_size:.0f}GB"
    return "N/A"

def extract_innodb_flush_log(content):
    """Extract innodb_flush_log_at_trx_commit value"""
    match = re.search(r'innodb_flush_log_at_trx_commit\s+(\d+)', content)
    return match.group(1) if match else "N/A"

def extract_all_performance_data(content):
    """Extract all test results for all thread counts"""
    lines = content.split('\n')
    results = {}
    
    for line in lines:
        if '| oltp_' in line and line.count('|') > 10:
            parts = [p.strip() for p in line.split('|')]
            if len(parts) > 3 and parts[1] and parts[2]:
                scenario = parts[1]
                threads = parts[2]
                if scenario not in results:
                    results[scenario] = {}
                results[scenario][threads] = {
                    'qps': parts[3] if len(parts) > 3 else '',
                    'tps': parts[4] if len(parts) > 4 else '',
                    'avg_latency': parts[5] if len(parts) > 5 else '',
                    'p95_latency': parts[6] if len(parts) > 6 else '',
                    'cpu_sirq': parts[7] if len(parts) > 7 else '',
                    'cpu_user': parts[8] if len(parts) > 8 else '',
                    'cpu_sys': parts[9] if len(parts) > 9 else '',
                    'cpu_wait': parts[10] if len(parts) > 10 else '',
                    'io_util': parts[11] if len(parts) > 11 else ''
                }
    
    return results

def extract_cpu_memory_info(content):
    """Extract CPU model, cores, and memory info"""
    cpu_match = re.search(r'型号名称：\s*(.+)', content)
    if not cpu_match:
        cpu_match = re.search(r'Model name:\s*(.+)', content)
    cpu_model = cpu_match.group(1).strip() if cpu_match else "N/A"
    
    # Support both "CPU(s):" and "CPU:" formats
    cores_match = re.search(r'CPU\(s\):\s*(\d+)', content)
    if not cores_match:
        cores_match = re.search(r'^CPU:\s+(\d+)', content, re.MULTILINE)
    cores = cores_match.group(1) if cores_match else "N/A"
    
    mem_match = re.search(r'Mem:\s+(\d+\w+)', content)
    memory = mem_match.group(1) if mem_match else "N/A"
    
    return cpu_model, cores, memory

def merge_reports(env_names):
    """Merge multiple performance reports with enhanced details"""
    
    # Read all reports
    reports = {}
    for env in env_names:
        file_path = f"{env}/performance_report.md"
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                reports[env] = f.read()
        else:
            print(f"Warning: {file_path} not found")
            return
    
    # Extract data for summary
    env_data = {}
    
    for env, content in reports.items():
        cpu_model, cores, memory = extract_cpu_memory_info(content)
        buffer_size = extract_innodb_buffer_pool_size(content)
        flush_log = extract_innodb_flush_log(content)
        perf_data = extract_all_performance_data(content)
        
        env_data[env] = {
            'cpu_model': cpu_model,
            'cores': cores,
            'memory': memory,
            'buffer_size': buffer_size,
            'flush_log': flush_log,
            'performance': perf_data
        }
    
    # Generate merged report
    output = f"""# MySQL Sysbench 性能测试综合报告 (详细版)

## 📊 执行摘要

本报告汇总了 **{len(env_names)}** 个不同环境下的MySQL性能测试结果，涵盖IDC自建机房、华为云和阿里云等多种部署场景。

### 测试环境概览

| 环境 | CPU型号 | 核数 | 内存 | Buffer Pool | Flush Log |
|------|---------|------|------|-------------|-----------|
"""
    
    for env in env_names:
        if env in env_data:
            data = env_data[env]
            output += f"| **{env}** | {data['cpu_model']} | {data['cores']} | {data['memory']} | {data['buffer_size']} | {data['flush_log']} |\n"
    
    output += """
### 测试配置

- **测试工具**: sysbench + tsar
- **测试数据集**: 16表 × 1000万行
- **测试时长**: 每场景30秒
- **测试场景**: 点查询、只读、读写混合、只写
- **并发级别**: 1, 8, 16, 32, 64, 128 线程

---

## 🏆 性能排名

### 点查询性能对比 (oltp_point_select)

"""
    
    # Point select comparison table
    output += "| 环境 | 1线程 | 8线程 | 16线程 | 32线程 | 64线程 | 128线程 |\n"
    output += "|------|-------|-------|--------|--------|--------|----------|\n"
    
    for env in env_names:
        if env in env_data and 'oltp_point_select' in env_data[env]['performance']:
            perf = env_data[env]['performance']['oltp_point_select']
            row = f"| **{env}** |"
            for threads in ['1', '8', '16', '32', '64', '128']:
                qps = perf.get(threads, {}).get('qps', '-')
                row += f" {qps} |"
            output += row + "\n"
    
    output += "\n### 只写性能对比 (oltp_write_only)\n\n"
    output += "| 环境 | 1线程 | 8线程 | 16线程 | 32线程 | 64线程 | 128线程 |\n"
    output += "|------|-------|-------|--------|--------|--------|----------|\n"
    
    for env in env_names:
        if env in env_data and 'oltp_write_only' in env_data[env]['performance']:
            perf = env_data[env]['performance']['oltp_write_only']
            row = f"| **{env}** |"
            for threads in ['1', '8', '16', '32', '64', '128']:
                qps = perf.get(threads, {}).get('qps', '-')
                row += f" {qps} |"
            output += row + "\n"
    
    output += "\n### 读写混合性能对比 (oltp_read_write)\n\n"
    output += "| 环境 | 1线程 | 8线程 | 16线程 | 32线程 | 64线程 | 128线程 |\n"
    output += "|------|-------|-------|--------|--------|--------|----------|\n"
    
    for env in env_names:
        if env in env_data and 'oltp_read_write' in env_data[env]['performance']:
            perf = env_data[env]['performance']['oltp_read_write']
            row = f"| **{env}** |"
            for threads in ['1', '8', '16', '32', '64', '128']:
                qps = perf.get(threads, {}).get('qps', '-')
                row += f" {qps} |"
            output += row + "\n"
    
    output += "\n### 只读性能对比 (oltp_read_only)\n\n"
    output += "| 环境 | 1线程 | 8线程 | 16线程 | 32线程 | 64线程 | 128线程 |\n"
    output += "|------|-------|-------|--------|--------|--------|----------|\n"
    
    for env in env_names:
        if env in env_data and 'oltp_read_only' in env_data[env]['performance']:
            perf = env_data[env]['performance']['oltp_read_only']
            row = f"| **{env}** |"
            for threads in ['1', '8', '16', '32', '64', '128']:
                qps = perf.get(threads, {}).get('qps', '-')
                row += f" {qps} |"
            output += row + "\n"
    
    output += """
---

## 📈 延迟分析

### 点查询延迟对比 (95%分位, ms)

| 环境 | 1线程 | 8线程 | 16线程 | 32线程 | 64线程 | 128线程 |
|------|-------|-------|--------|--------|--------|----------|
"""
    
    for env in env_names:
        if env in env_data and 'oltp_point_select' in env_data[env]['performance']:
            perf = env_data[env]['performance']['oltp_point_select']
            row = f"| **{env}** |"
            for threads in ['1', '8', '16', '32', '64', '128']:
                latency = perf.get(threads, {}).get('p95_latency', '-')
                row += f" {latency} |"
            output += row + "\n"
    
    output += "\n### 读写混合延迟对比 (95%分位, ms)\n\n"
    output += "| 环境 | 1线程 | 8线程 | 16线程 | 32线程 | 64线程 | 128线程 |\n"
    output += "|------|-------|-------|--------|--------|--------|----------|\n"
    
    for env in env_names:
        if env in env_data and 'oltp_read_write' in env_data[env]['performance']:
            perf = env_data[env]['performance']['oltp_read_write']
            row = f"| **{env}** |"
            for threads in ['1', '8', '16', '32', '64', '128']:
                latency = perf.get(threads, {}).get('p95_latency', '-')
                row += f" {latency} |"
            output += row + "\n"
    
    output += """
---

## 💡 关键发现

### 性能特点

1. **CPU架构影响**
   - 不同CPU架构在各场景下表现差异明显
   - 单核性能对点查询场景影响显著

2. **事务持久化设置**
   - innodb_flush_log_at_trx_commit=1 vs 2 对写入性能影响明显
   - 建议根据业务对数据安全性要求选择合适配置

3. **并发扩展性**
   - 各环境在不同并发级别下的扩展性表现不同
   - 需要根据实际业务并发选择合适的硬件配置

4. **延迟控制**
   - 高并发下延迟控制能力体现系统稳定性
   - 95%分位延迟是衡量用户体验的重要指标

### 环境推荐

"""
    
    # Find best performers
    best_point_select = max(env_names, key=lambda x: int(env_data[x]['performance'].get('oltp_point_select', {}).get('128', {}).get('qps', '0').replace(',', '')) if env_data[x]['performance'].get('oltp_point_select', {}).get('128', {}).get('qps', '0').replace(',', '').isdigit() else 0)
    best_write = max(env_names, key=lambda x: int(env_data[x]['performance'].get('oltp_write_only', {}).get('128', {}).get('qps', '0').replace(',', '')) if env_data[x]['performance'].get('oltp_write_only', {}).get('128', {}).get('qps', '0').replace(',', '').isdigit() else 0)
    
    output += f"- **查询密集型业务**: 推荐 **{best_point_select}** 环境\n"
    output += f"- **写入密集型业务**: 推荐 **{best_write}** 环境\n"
    output += "- **混合负载**: 需要综合考虑QPS、延迟和成本\n"
    
    output += """
---

## 📊 64线程性能对比

| 测试场景 | idc | idc.trx1 | huawei | aliyun | aliyun.trx1 |
|---------|-----|----------|--------|--------|-------------|
"""
    
    # Add 64-thread comparison for all scenarios
    scenarios = ['oltp_point_select', 'oltp_read_only', 'oltp_read_write', 'oltp_write_only']
    scenario_names = {
        'oltp_point_select': '点查询',
        'oltp_read_only': '只读',
        'oltp_read_write': '读写混合',
        'oltp_write_only': '只写'
    }
    
    for scenario in scenarios:
        row = f"| **{scenario_names.get(scenario, scenario)}** |"
        for env in env_names:
            if env in env_data and scenario in env_data[env]['performance']:
                qps = env_data[env]['performance'][scenario].get('64', {}).get('qps', '-')
                row += f" {qps} |"
            else:
                row += " - |"
        output += row + "\n"
    
    output += "\n---\n\n"
    
    # Add individual chapters with full details
    for i, env in enumerate(env_names, 1):
        if env in reports:
            chapter_num = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十'][i-1]
            output += f"# 第{chapter_num}章：{env} 环境详细报告\n\n"
            
            # Extract content after first header
            content = reports[env]
            lines = content.split('\n')
            start_idx = 0
            for j, line in enumerate(lines):
                if line.startswith('**测试时间**'):
                    start_idx = j
                    break
            
            chapter_content = '\n'.join(lines[start_idx:])
            
            # Process chapter content
            chapter_lines = chapter_content.split('\n')
            processed_lines = []
            in_table = False
            skip_section = False
            
            for line in chapter_lines:
                # Skip duplicate sections and timestamp placeholders
                if (line.startswith('### 监控数据说明') or 
                    line.startswith('## 测试结果分析') or 
                    line.startswith('### 性能指标') or
                    line.startswith('### 系统监控指标') or
                    line.startswith('### 关键发现') or
                    line.startswith('## 说明') or
                    '*报告生成时间' in line):
                    skip_section = True
                    if '*报告生成时间' in line:
                        continue
                    continue
                elif skip_section and (line.startswith('#') or line.startswith('---')):
                    skip_section = False
                elif skip_section:
                    continue
                
                # Process table
                if '| 测试场景 | 并发数 | QPS |' in line:
                    in_table = True
                    parts = line.split('|')
                    if '监控样本数' in line:
                        new_parts = [p for p in parts if '监控样本数' not in p]
                        processed_lines.append('|'.join(new_parts))
                    else:
                        processed_lines.append(line)
                elif in_table and line.startswith('|------'):
                    parts = line.split('|')
                    if len(parts) > 13:
                        new_parts = parts[:12] + parts[13:]
                        processed_lines.append('|'.join(new_parts))
                    else:
                        processed_lines.append(line)
                elif in_table and line.startswith('| oltp_'):
                    parts = line.split('|')
                    if len(parts) > 13:
                        new_parts = parts[:12] + parts[13:]
                        processed_lines.append('|'.join(new_parts))
                    else:
                        processed_lines.append(line)
                elif in_table and (line.strip() == '' or not line.startswith('|')):
                    in_table = False
                    processed_lines.append(line)
                else:
                    processed_lines.append(line)
            
            output += '\n'.join(processed_lines)
            output += "\n\n---\n\n"
    
    # Add appendix
    output += """
# 附录：监控指标说明

## 监控数据说明

| 报告列名 | tsar对应列 | 说明 |
|---------|-----------|------|
| CPU软中断(%) | sirq | 软中断CPU使用率 |
| CPU用户(%) | user | 用户态CPU使用率 |
| CPU系统(%) | sys | 内核态CPU使用率 |
| CPU等待(%) | wait | IO等待时间占用的CPU |
| IO利用率(%) | util (IO部分) | 磁盘IO使用率 |

## 性能指标说明

- **QPS (Queries Per Second)**: 每秒查询数，衡量数据库处理查询的能力
- **TPS (Transactions Per Second)**: 每秒事务数，与QPS在点查询场景下相等
- **平均延迟**: 所有请求的平均响应时间
- **95%延迟**: 95%的请求响应时间不超过此值，更能反映用户体验

## 测试场景说明

| 场景 | 描述 | 主要指标 |
|------|------|----------|
| oltp_point_select | 主键点查询 | QPS, 延迟 |
| oltp_read_only | 只读事务(包含多表JOIN) | TPS, QPS |
| oltp_read_write | 读写混合事务 | TPS, 延迟 |
| oltp_write_only | 只写事务 | TPS, IO利用率 |

## 数据来源说明

- CPU/IO数据来源于tsar监控日志，按测试时间段精确匹配并计算平均值
- 系统监控数据与性能数据时间精确对应，确保数据准确性
- 测试使用sysbench工具，针对MySQL数据库进行标准化性能测试

---

"""
    
    # Add timestamp
    output += f"*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
    
    # Write output
    with open('mysql_sysbench_v2.md', 'w', encoding='utf-8') as f:
        f.write(output)
    
    print(f"详细版合并报告已生成: mysql_sysbench_v2.md")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 merge_reports_v2.py env1,env2,env3,...")
        sys.exit(1)
    
    env_names = sys.argv[1].split(',')
    merge_reports(env_names)
