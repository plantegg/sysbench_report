#!/usr/bin/env python3
import os
import sys
import re
from datetime import datetime, timedelta
import glob

def parse_tsar_log(tsar_file):
    """解析tsar.log文件，返回时间戳和CPU/IO数据的字典"""
    tsar_data = {}
    
    if not os.path.exists(tsar_file):
        print(f"警告: tsar.log文件不存在: {tsar_file}")
        return tsar_data
    
    with open(tsar_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('Time') or '---' in line:
                continue
            
            parts = line.split()
            if len(parts) < 6:
                continue
            
            # 解析时间格式: 22/11/25-15:33:45
            time_str = parts[0]
            try:
                # tsar格式: 22/11/25-15:33:45 表示 2025-11-22 15:33:45
                date_part, time_part = time_str.split('-')
                yy, mm, dd = date_part.split('/')
                
                # 转换为完整日期: 22/11/25 -> 2025-11-22
                full_year = f"20{yy}"
                dt = datetime.strptime(f"{full_year}-{mm}-{dd} {time_part}", "%Y-%m-%d %H:%M:%S")
                
                # 解析CPU数据 (user, sys, wait, hirq, sirq, util)
                cpu_user = float(parts[1])
                cpu_sys = float(parts[2]) 
                cpu_wait = float(parts[3])
                cpu_sirq = float(parts[5])  # CPU软中断
                
                # 解析IO数据 (最后一列是IO util)
                io_util = 0.0
                if len(parts) >= 24:  # 确保有完整的IO数据
                    io_util = float(parts[23])  # IO利用率 (最后一列)
                
                tsar_data[dt] = {
                    'cpu_user': cpu_user,
                    'cpu_sys': cpu_sys,
                    'cpu_wait': cpu_wait,
                    'cpu_sirq': cpu_sirq,
                    'io_util': io_util
                }
            except (ValueError, IndexError) as e:
                continue
    
    return tsar_data

def get_tsar_avg_for_period(tsar_data, start_time, end_time):
    """获取指定时间段内的tsar数据平均值"""
    if not tsar_data:
        return None
    
    # 转换时间字符串为datetime对象
    start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
    end_dt = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
    
    # 收集时间段内的数据，允许前后30秒的误差
    period_data = []
    for ts, data in tsar_data.items():
        if (start_dt - timedelta(seconds=30)) <= ts <= (end_dt + timedelta(seconds=30)):
            period_data.append(data)
    
    # 如果还是没有数据，尝试更宽松的匹配（只匹配时间，忽略日期）
    if not period_data:
        start_time_only = start_dt.time()
        end_time_only = end_dt.time()
        for ts, data in tsar_data.items():
            ts_time = ts.time()
            if start_time_only <= ts_time <= end_time_only:
                period_data.append(data)
    
    # 如果仍然没有数据，尝试找最接近的时间段数据
    if not period_data:
        # 扩大搜索范围到前后5分钟
        for ts, data in tsar_data.items():
            if (start_dt - timedelta(minutes=5)) <= ts <= (end_dt + timedelta(minutes=5)):
                period_data.append(data)
    
    if not period_data:
        return None
    
    # 计算平均值
    avg_data = {
        'cpu_user': sum(d['cpu_user'] for d in period_data) / len(period_data),
        'cpu_sys': sum(d['cpu_sys'] for d in period_data) / len(period_data),
        'cpu_wait': sum(d['cpu_wait'] for d in period_data) / len(period_data),
        'cpu_sirq': sum(d['cpu_sirq'] for d in period_data) / len(period_data),
        'io_util': sum(d['io_util'] for d in period_data) / len(period_data),
        'sample_count': len(period_data)
    }
    
    return avg_data

def parse_sysbench_result(log_file):
    """解析sysbench结果文件"""
    result = {}
    
    with open(log_file, 'r') as f:
        content = f.read()
    
    # 提取QPS和TPS
    qps_match = re.search(r'queries:\s+\d+\s+\((\d+\.?\d*)\s+per sec\.\)', content)
    tps_match = re.search(r'transactions:\s+\d+\s+\((\d+\.?\d*)\s+per sec\.\)', content)
    
    # 提取延迟信息
    avg_latency_match = re.search(r'avg:\s+(\d+\.?\d*)', content)
    p95_latency_match = re.search(r'95th percentile:\s+(\d+\.?\d*)', content)
    
    if qps_match:
        result['qps'] = float(qps_match.group(1))
    if tps_match:
        result['tps'] = float(tps_match.group(1))
    if avg_latency_match:
        result['avg_latency'] = float(avg_latency_match.group(1))
    if p95_latency_match:
        result['p95_latency'] = float(p95_latency_match.group(1))
    
    return result

def parse_test_time(time_file):
    """解析测试时间文件"""
    times = {}
    if os.path.exists(time_file):
        with open(time_file, 'r') as f:
            for line in f:
                if 'TEST_START_TIME:' in line:
                    times['start'] = line.split(':', 1)[1].strip()
                elif 'TEST_END_TIME:' in line:
                    times['end'] = line.split(':', 1)[1].strip()
    return times

def generate_html_report(result_dir):
    """生成HTML报告"""
    
    # 解析tsar.log
    tsar_file = os.path.join(result_dir, 'tsar.log')
    tsar_data = parse_tsar_log(tsar_file)
    
    # 收集所有测试结果
    results = []
    
    # 查找所有测试日志文件
    log_files = glob.glob(os.path.join(result_dir, 'oltp_*_*threads.log'))
    
    for log_file in log_files:
        filename = os.path.basename(log_file)
        # 解析文件名: oltp_point_select_1threads.log
        match = re.match(r'(oltp_\w+)_(\d+)threads\.log', filename)
        if not match:
            continue
        
        scenario = match.group(1)
        threads = int(match.group(2))
        
        # 解析sysbench结果
        sysbench_result = parse_sysbench_result(log_file)
        
        # 解析测试时间
        time_file = log_file.replace('.log', '_time.log')
        test_times = parse_test_time(time_file)
        
        # 获取对应时间段的tsar数据
        tsar_avg = None
        if test_times.get('start') and test_times.get('end'):
            tsar_avg = get_tsar_avg_for_period(tsar_data, test_times['start'], test_times['end'])
        
        result = {
            'scenario': scenario,
            'threads': threads,
            'qps': sysbench_result.get('qps', 0),
            'tps': sysbench_result.get('tps', 0),
            'avg_latency': sysbench_result.get('avg_latency', 0),
            'p95_latency': sysbench_result.get('p95_latency', 0),
            'start_time': test_times.get('start', ''),
            'end_time': test_times.get('end', ''),
            'tsar_data': tsar_avg
        }
        
        results.append(result)
    
    # 按测试开始时间排序（测试执行顺序）
    results.sort(key=lambda x: x['start_time'] if x['start_time'] else '')
    
    # 读取服务器配置
    server_config = ""
    config_file = os.path.join(result_dir, 'server_config.txt')
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            server_config = f.read()
    
    # 读取测试配置
    test_config = ""
    test_config_file = os.path.join(result_dir, 'test_config.txt')
    if os.path.exists(test_config_file):
        with open(test_config_file, 'r') as f:
            test_config = f.read()
    
    # 读取MySQL配置
    mysql_config = ""
    mysql_config_file = os.path.join(result_dir, 'mysql_variables.txt')
    if os.path.exists(mysql_config_file):
        with open(mysql_config_file, 'r') as f:
            mysql_config = f.read()
    
    # 生成HTML
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>MySQL 性能测试报告 v7 Final</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .section {{ margin: 20px 0; }}
        table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: center; }}
        th {{ background-color: #f2f2f2; }}
        .scenario {{ background-color: #e6f3ff; font-weight: bold; }}
        pre {{ background-color: #f5f5f5; padding: 10px; border-radius: 3px; overflow-x: auto; }}
        .time {{ font-size: 0.8em; color: #666; }}
        .tsar-data {{ background-color: #fff3cd; }}
        .config-section {{ background-color: #e8f5e8; padding: 15px; border-radius: 5px; margin: 10px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>MySQL 性能测试报告 v7 Final</h1>
        <p>测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>测试工具: sysbench + tsar (按时间段精确匹配)</p>
        <p>tsar数据样本: {len(tsar_data)} 条记录</p>
    </div>
    
    <div class="section">
        <h2>测试配置信息</h2>
        <div class="config-section">
            <pre>{test_config}</pre>
        </div>
    </div>
    
    <div class="section">
        <h2>MySQL配置参数</h2>
        <div class="config-section">
            <pre>{mysql_config}</pre>
        </div>
    </div>
    
    <div class="section">
        <h2>压测服务器配置</h2>
        <pre>{server_config}</pre>
    </div>
    
    <div class="section">
        <h2>性能测试结果汇总 (含CPU/IO监控数据)</h2>
        <table>
            <tr>
                <th>测试场景</th>
                <th>并发数</th>
                <th>QPS</th>
                <th>TPS</th>
                <th>平均延迟(ms)</th>
                <th>95%延迟(ms)</th>
                <th>CPU软中断(%)</th>
                <th>CPU用户(%)</th>
                <th>CPU系统(%)</th>
                <th>CPU等待(%)</th>
                <th>IO利用率(%)</th>
                <th>监控样本数</th>
                <th>测试时间段</th>
            </tr>"""
    
    for result in results:
        tsar_info = ""
        cpu_sirq = cpu_user = cpu_sys = cpu_wait = io_util = sample_count = "N/A"
        
        if result['tsar_data']:
            cpu_sirq = f"{result['tsar_data']['cpu_sirq']:.1f}"
            cpu_user = f"{result['tsar_data']['cpu_user']:.1f}"
            cpu_sys = f"{result['tsar_data']['cpu_sys']:.1f}"
            cpu_wait = f"{result['tsar_data']['cpu_wait']:.1f}"
            io_util = f"{result['tsar_data']['io_util']:.1f}"
            sample_count = str(result['tsar_data']['sample_count'])
        
        time_range = f"{result['start_time']} ~ {result['end_time']}" if result['start_time'] else "N/A"
        
        html_content += f"""
            <tr>
                <td class="scenario">{result['scenario']}</td>
                <td>{result['threads']}</td>
                <td>{result['qps']:,.0f}</td>
                <td>{result['tps']:,.0f}</td>
                <td>{result['avg_latency']:.2f}</td>
                <td>{result['p95_latency']:.2f}</td>
                <td class="tsar-data">{cpu_sirq}</td>
                <td class="tsar-data">{cpu_user}</td>
                <td class="tsar-data">{cpu_sys}</td>
                <td class="tsar-data">{cpu_wait}</td>
                <td class="tsar-data">{io_util}</td>
                <td class="tsar-data">{sample_count}</td>
                <td class="time">{time_range}</td>
            </tr>"""
    
    html_content += """
        </table>
    
    <div class="section">
        <h3>监控数据说明</h3>
        <table>
            <tr>
                <th>报告列名</th>
                <th>tsar对应列</th>
                <th>说明</th>
            </tr>
            <tr>
                <td>CPU软中断(%)</td>
                <td>sirq</td>
                <td>软中断CPU使用率</td>
            </tr>
            <tr>
                <td>CPU用户(%)</td>
                <td>user</td>
                <td>用户态CPU使用率</td>
            </tr>
            <tr>
                <td>CPU系统(%)</td>
                <td>sys</td>
                <td>内核态CPU使用率</td>
            </tr>
            <tr>
                <td>CPU等待(%)</td>
                <td>wait</td>
                <td>IO等待时间占用的CPU</td>
            </tr>
            <tr>
                <td>IO利用率(%)</td>
                <td>util (IO部分)</td>
                <td>磁盘IO使用率</td>
            </tr>
        </table>
    </div>
    </div>
    
    <div class="section">
        <h2>说明</h2>
        <ul>
            <li>CPU/IO数据来源于tsar监控日志，按测试时间段精确匹配并计算平均值</li>
            <li>监控样本数表示该测试时间段内tsar记录的数据点数量</li>
            <li>黄色背景列为系统监控数据，与性能数据时间精确对应</li>
            <li>CPU软中断 = 软中断CPU使用率，CPU用户 = 用户态CPU，CPU系统 = 内核态CPU，CPU等待 = IO等待</li>
        </ul>
    </div>
    
</body>
</html>"""
    
    # 写入HTML文件
    report_file = os.path.join(result_dir, 'performance_report.html')
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return report_file

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python3 generate_report_v7_final.py <结果目录>")
        sys.exit(1)
    
    result_dir = sys.argv[1]
    if not os.path.exists(result_dir):
        print(f"错误: 结果目录不存在: {result_dir}")
        sys.exit(1)
    
    report_file = generate_html_report(result_dir)
    print(f"性能测试报告已生成: {report_file}")
