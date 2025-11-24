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

def extract_peak_performance(content):
    """Extract peak QPS for point_select and write_only at 128 threads"""
    lines = content.split('\n')
    point_select_qps = 0
    write_only_qps = 0
    
    for line in lines:
        if '| oltp_point_select | 128 |' in line:
            parts = line.split('|')
            if len(parts) > 3:
                point_select_qps = parts[3].strip().replace(',', '')
        elif '| oltp_write_only | 128 |' in line:
            parts = line.split('|')
            if len(parts) > 3:
                write_only_qps = parts[3].strip().replace(',', '')
    
    return point_select_qps, write_only_qps

def extract_cpu_memory_info(content):
    """Extract CPU model, cores, and memory info"""
    cpu_match = re.search(r'型号名称：\s*(.+)', content)
    if not cpu_match:
        cpu_match = re.search(r'Model name:\s*(.+)', content)
    cpu_model = cpu_match.group(1).strip() if cpu_match else "N/A"
    
    cores_match = re.search(r'CPU\(s\):\s*(\d+)', content)
    cores = cores_match.group(1) if cores_match else "N/A"
    
    mem_match = re.search(r'Mem:\s+(\d+\w+)', content)
    memory = mem_match.group(1) if mem_match else "N/A"
    
    return cpu_model, cores, memory

def extract_summary_table_rows(content, env_name):
    """Extract 128-thread test results and add environment column"""
    lines = content.split('\n')
    rows = []
    
    for line in lines:
        if '| oltp_' in line and '| 128 |' in line:
            # Remove monitoring sample count column and add environment
            parts = line.split('|')
            if len(parts) >= 13:
                # Remove the monitoring sample count column (index 11)
                new_parts = parts[:11] + parts[12:13] + [f' {env_name} '] + parts[13:]
                rows.append('|'.join(new_parts))
    
    return rows

def merge_reports(env_names):
    """Merge multiple performance reports"""
    
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
    all_summary_rows = []
    
    for env, content in reports.items():
        cpu_model, cores, memory = extract_cpu_memory_info(content)
        point_qps, write_qps = extract_peak_performance(content)
        buffer_size = extract_innodb_buffer_pool_size(content)
        
        env_data[env] = {
            'cpu_model': cpu_model,
            'cores': cores,
            'memory': memory,
            'point_qps': point_qps,
            'write_qps': write_qps,
            'buffer_size': buffer_size
        }
        
        # Extract summary table rows
        summary_rows = extract_summary_table_rows(content, env)
        all_summary_rows.extend(summary_rows)
    
    # Generate merged report
    output = f"""# MySQL Sysbench 性能测试综合报告

## 摘要

本报告汇总了{len(env_names)}个不同环境下的MySQL性能测试结果，涵盖了IDC自建机房、华为云和阿里云等多种部署场景。测试使用sysbench工具进行标准化性能评估，包含点查询、只读、读写混合、只写四种典型业务场景。

**测试环境概览:**
"""
    
    for env in env_names:
        if env in env_data:
            data = env_data[env]
            output += f"- **{env}**: {data['cpu_model']} ({data['cores']}核) + {data['memory']}内存\n"
    
    output += f"""
**关键配置:**
- 所有环境均使用{env_data[env_names[0]]['buffer_size']} InnoDB缓冲池
- 测试数据集：16表 × 1000万行
- 测试时长：每场景30秒

## 数据总结与结论

### 性能表现排名

**点查询性能 (128并发QPS):**
"""
    
    # Sort by point select performance
    sorted_envs = sorted(env_names, key=lambda x: int(env_data[x]['point_qps'].replace(',', '')) if env_data[x]['point_qps'].isdigit() or env_data[x]['point_qps'].replace(',', '').isdigit() else 0, reverse=True)
    
    for i, env in enumerate(sorted_envs, 1):
        if env in env_data:
            output += f"{i}. {env}: {env_data[env]['point_qps']} QPS\n"
    
    output += f"""
**只写性能 (128并发QPS):**
"""
    
    # Sort by write performance  
    sorted_envs_write = sorted(env_names, key=lambda x: int(env_data[x]['write_qps'].replace(',', '')) if env_data[x]['write_qps'].isdigit() or env_data[x]['write_qps'].replace(',', '').isdigit() else 0, reverse=True)
    
    for i, env in enumerate(sorted_envs_write, 1):
        if env in env_data:
            output += f"{i}. {env}: {env_data[env]['write_qps']} QPS\n"

    output += """
### 关键发现

1. **CPU架构影响显著**: 不同CPU架构在各场景下表现差异明显
2. **事务持久化设置影响**: innodb_flush_log_at_trx_commit设置对写入性能有显著影响
3. **资源配置差异**: 核数多不一定性能好，单核性能同样重要
4. **IO瓶颈明显**: 写入密集场景下IO利用率成为主要瓶颈
5. **延迟控制**: 高并发下延迟控制能力体现系统稳定性

## 关键指标对比

| 环境 | CPU型号 | 核数 | 内存 | 点查询峰值QPS | 只写峰值QPS | innodb_buffer_pool_size |
|------|---------|------|------|---------------|-------------|-------------------------|
"""
    
    for env in env_names:
        if env in env_data:
            data = env_data[env]
            output += f"| {env} | {data['cpu_model']} | {data['cores']} | {data['memory']} | {data['point_qps']} | {data['write_qps']} | {data['buffer_size']} |\n"
    
    output += """
## 性能测试结果汇总

| 测试场景 | 并发数 | QPS | TPS | 平均延迟(ms) | 95%延迟(ms) | CPU利用率(%) | CPU用户(%) | CPU系统(%) | CPU等待(%) | IO利用率(%) | 环境 | 测试时间段 |
|---------|--------|-----|-----|-------------|-------------|-------------|------------|------------|------------|-------------|------|------------|
"""
    
    for row in all_summary_rows:
        output += row + '\n'
    
    output += "\n---\n\n"
    
    # Add individual chapters
    for i, env in enumerate(env_names, 1):
        if env in reports:
            output += f"# 第{['一', '二', '三', '四', '五', '六', '七', '八', '九', '十'][i-1]}章：{env}\n\n"
            
            # Extract content after first header
            content = reports[env]
            lines = content.split('\n')
            start_idx = 0
            for j, line in enumerate(lines):
                if line.startswith('**测试时间**'):
                    start_idx = j
                    break
            
            chapter_content = '\n'.join(lines[start_idx:])
            
            # Remove monitoring sample count column from tables
            chapter_lines = chapter_content.split('\n')
            processed_lines = []
            in_table = False
            skip_section = False
            
            for line in chapter_lines:
                # Skip all duplicate sections
                if (line.startswith('### 监控数据说明') or 
                    line.startswith('## 测试结果分析') or 
                    line.startswith('### 性能指标') or
                    line.startswith('### 系统监控指标') or
                    line.startswith('### 关键发现') or
                    line.startswith('## 说明')):
                    skip_section = True
                    continue
                elif skip_section and (line.startswith('#') or line.startswith('---') or line.startswith('*报告生成时间')):
                    skip_section = False
                    if line.startswith('*报告生成时间'):
                        continue  # Skip the timestamp line too
                elif skip_section:
                    continue
                
                # Check if we're in the main performance table
                if '| 测试场景 | 并发数 | QPS |' in line:
                    in_table = True
                    # Remove 监控样本数 column from header
                    parts = line.split('|')
                    if '监控样本数' in line:
                        # Find and remove 监控样本数 column
                        new_parts = []
                        for part in parts:
                            if '监控样本数' not in part:
                                new_parts.append(part)
                        processed_lines.append('|'.join(new_parts))
                    else:
                        processed_lines.append(line)
                elif in_table and line.startswith('|------'):
                    # Remove corresponding separator
                    parts = line.split('|')
                    if len(parts) > 12:  # Has monitoring sample count column
                        new_parts = parts[:11] + parts[12:]
                        processed_lines.append('|'.join(new_parts))
                    else:
                        processed_lines.append(line)
                elif in_table and line.startswith('| oltp_'):
                    # Remove monitoring sample count data
                    parts = line.split('|')
                    if len(parts) > 12:  # Has monitoring sample count column
                        new_parts = parts[:11] + parts[12:]
                        processed_lines.append('|'.join(new_parts))
                    else:
                        processed_lines.append(line)
                elif in_table and (line.strip() == '' or not line.startswith('|')):
                    # End of table
                    in_table = False
                    processed_lines.append(line)
                else:
                    processed_lines.append(line)
            
            output += '\n'.join(processed_lines)
            output += "\n\n---\n\n"
    
    # Add monitoring data explanation and analysis at the end
    output += """
## 监控数据说明

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
- 系统监控数据与性能数据时间精确对应，确保数据准确性
- 测试使用sysbench工具，针对MySQL数据库进行标准化性能测试

---
"""
    
    # Add timestamp
    output += f"*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
    
    # Write output
    with open('mysql_sysbench.md', 'w', encoding='utf-8') as f:
        f.write(output)
    
    print(f"合并报告已生成: mysql_sysbench.md")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 merge_reports.py env1,env2,env3,...")
        sys.exit(1)
    
    env_names = sys.argv[1].split(',')
    merge_reports(env_names)
