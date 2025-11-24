#!/bin/bash

# MySQL 性能压测脚本 - 不杀掉现有tsar进程
set -e

# 加载配置文件
load_config() {
    local config_file="$1"
    if [ -f "$config_file" ]; then
        echo "加载配置文件: $config_file"
        source "$config_file"
    else
        echo "配置文件不存在: $config_file，使用默认配置"
        MYSQL_HOST="10.127.33.154"
        MYSQL_PORT="3316"
        MYSQL_USER="ren"
        MYSQL_PASSWORD="123"
        MYSQL_DB="sbtest"
        TABLES=16
        TABLE_SIZE=100000
        TEST_TIME=10
        NEED_PREPARE="true"
        SCENARIOS="oltp_point_select oltp_read_only oltp_read_write oltp_write_only"
        THREADS="1 128"
    fi
}

# 解析参数
CONFIG_FILE="${1:-benchmark_config.conf}"
OVERRIDE_TEST_TIME="$2"
OVERRIDE_NEED_PREPARE="$3"

# 加载配置
load_config "$CONFIG_FILE"

# 覆盖参数
if [ -n "$OVERRIDE_TEST_TIME" ]; then
    TEST_TIME="$OVERRIDE_TEST_TIME"
fi

if [ -n "$OVERRIDE_NEED_PREPARE" ]; then
    NEED_PREPARE="$OVERRIDE_NEED_PREPARE"
fi

# 转换为数组
SCENARIOS_ARRAY=($SCENARIOS)
THREADS_ARRAY=($THREADS)

# 结果目录
RESULT_DIR="mysql_benchmark_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$RESULT_DIR"

echo "=== MySQL 性能压测开始 ===" | tee "$RESULT_DIR/benchmark.log"
echo "时间: $(date)" | tee -a "$RESULT_DIR/benchmark.log"
echo "目标服务器: $MYSQL_HOST:$MYSQL_PORT" | tee -a "$RESULT_DIR/benchmark.log"
echo "数据准备模式: $NEED_PREPARE" | tee -a "$RESULT_DIR/benchmark.log"
echo "测试时间: ${TEST_TIME}秒" | tee -a "$RESULT_DIR/benchmark.log"
echo "表大小: ${TABLE_SIZE}行" | tee -a "$RESULT_DIR/benchmark.log"

# 获取压测服务器配置
echo "=== 压测服务器配置 ===" | tee -a "$RESULT_DIR/benchmark.log"
echo "=== CPU 信息 ===" > "$RESULT_DIR/server_config.txt"
lscpu >> "$RESULT_DIR/server_config.txt"
echo >> "$RESULT_DIR/server_config.txt"
echo "=== 内存信息 ===" >> "$RESULT_DIR/server_config.txt"
free -h >> "$RESULT_DIR/server_config.txt"

# 测试 MySQL 连接
echo "=== 测试 MySQL 连接 ===" | tee -a "$RESULT_DIR/benchmark.log"
mysql -h $MYSQL_HOST -P $MYSQL_PORT -u $MYSQL_USER -p"$MYSQL_PASSWORD" -e "SELECT VERSION();" > "$RESULT_DIR/mysql_version.txt" 2>&1

# 检查tsar是否在运行（不启动新的tsar）
echo "=== 检查tsar监控状态 ===" | tee -a "$RESULT_DIR/benchmark.log"
ssh root@$MYSQL_HOST "ps aux | grep tsar | grep -v grep || echo 'tsar未运行'" | tee -a "$RESULT_DIR/benchmark.log"

# 获取MySQL配置参数
echo "=== 获取MySQL配置参数 ===" | tee -a "$RESULT_DIR/benchmark.log"
mysql -h $MYSQL_HOST -P $MYSQL_PORT -u $MYSQL_USER -p"$MYSQL_PASSWORD" -e "SHOW VARIABLES WHERE Variable_name IN ('innodb_buffer_pool_size', 'innodb_flush_log_at_trx_commit');" > "$RESULT_DIR/mysql_variables.txt" 2>&1

# 记录测试配置信息
echo "=== 测试配置信息 ===" > "$RESULT_DIR/test_config.txt"
echo "MYSQL_HOST: $MYSQL_HOST" >> "$RESULT_DIR/test_config.txt"
echo "MYSQL_PORT: $MYSQL_PORT" >> "$RESULT_DIR/test_config.txt"
echo "TABLES: $TABLES" >> "$RESULT_DIR/test_config.txt"
echo "TABLE_SIZE: $TABLE_SIZE" >> "$RESULT_DIR/test_config.txt"
echo "TEST_TIME: $TEST_TIME" >> "$RESULT_DIR/test_config.txt"

# 数据库准备
if [ "$NEED_PREPARE" = "true" ]; then
    echo "=== 重建数据库 ===" | tee -a "$RESULT_DIR/benchmark.log"
    mysql -h $MYSQL_HOST -P $MYSQL_PORT -u $MYSQL_USER -p"$MYSQL_PASSWORD" -e "DROP DATABASE IF EXISTS $MYSQL_DB;" 2>&1 | tee -a "$RESULT_DIR/benchmark.log"
    mysql -h $MYSQL_HOST -P $MYSQL_PORT -u $MYSQL_USER -p"$MYSQL_PASSWORD" -e "CREATE DATABASE $MYSQL_DB;" 2>&1 | tee -a "$RESULT_DIR/benchmark.log"
    
    echo "=== 准备测试数据 ===" | tee -a "$RESULT_DIR/benchmark.log"
    echo "准备测试数据（${TABLES}表×${TABLE_SIZE}行）..." | tee -a "$RESULT_DIR/benchmark.log"
    sysbench oltp_common \
      --mysql-host=$MYSQL_HOST \
      --mysql-port=$MYSQL_PORT \
      --mysql-user=$MYSQL_USER \
      --mysql-password="$MYSQL_PASSWORD" \
      --mysql-db=$MYSQL_DB \
      --tables=$TABLES \
      --table-size=$TABLE_SIZE \
      prepare 2>&1 | tee "$RESULT_DIR/prepare.log"
else
    echo "=== 使用现有数据库 ===" | tee -a "$RESULT_DIR/benchmark.log"
    mysql -h $MYSQL_HOST -P $MYSQL_PORT -u $MYSQL_USER -p"$MYSQL_PASSWORD" -e "CREATE DATABASE IF NOT EXISTS $MYSQL_DB;" 2>&1 | tee -a "$RESULT_DIR/benchmark.log"
fi

# 执行完整压测
for scenario in "${SCENARIOS_ARRAY[@]}"; do
    echo "=== 压测场景: $scenario ===" | tee -a "$RESULT_DIR/benchmark.log"
    
    for thread in "${THREADS_ARRAY[@]}"; do
        test_name="${scenario}_${thread}threads"
        echo "--- 并发数: $thread ---" | tee -a "$RESULT_DIR/benchmark.log"
        
        # 记录测试开始时间
        TEST_START_TIME=$(date '+%Y-%m-%d %H:%M:%S')
        echo "测试开始时间: $TEST_START_TIME" | tee -a "$RESULT_DIR/benchmark.log"
        echo "TEST_START_TIME: $TEST_START_TIME" > "$RESULT_DIR/${test_name}_time.log"
        
        # 执行压测
        sysbench $scenario \
          --threads=$thread \
          --mysql-host=$MYSQL_HOST \
          --mysql-port=$MYSQL_PORT \
          --mysql-user=$MYSQL_USER \
          --mysql-password="$MYSQL_PASSWORD" \
          --mysql-db=$MYSQL_DB \
          --tables=$TABLES \
          --table-size=$TABLE_SIZE \
          --report-interval=1 \
          --time=$TEST_TIME \
          run 2>&1 | tee "$RESULT_DIR/${test_name}.log"
        
        # 记录测试结束时间
        TEST_END_TIME=$(date '+%Y-%m-%d %H:%M:%S')
        echo "测试结束时间: $TEST_END_TIME" | tee -a "$RESULT_DIR/benchmark.log"
        echo "TEST_END_TIME: $TEST_END_TIME" >> "$RESULT_DIR/${test_name}_time.log"
        
        echo "完成: $test_name" | tee -a "$RESULT_DIR/benchmark.log"
        sleep 2  # 间隔休息
    done
done

# 下载tsar监控数据（不停止tsar进程）
echo "=== 下载tsar监控数据 ===" | tee -a "$RESULT_DIR/benchmark.log"
scp root@$MYSQL_HOST:/tmp/tsar.log "$RESULT_DIR/" 2>/dev/null || echo "无法从$MYSQL_HOST下载tsar.log" | tee -a "$RESULT_DIR/benchmark.log"

echo "=== 压测完成 ===" | tee -a "$RESULT_DIR/benchmark.log"
TOTAL_END_TIME=$(date '+%Y-%m-%d %H:%M:%S')
echo "总体结束时间: $TOTAL_END_TIME" | tee -a "$RESULT_DIR/benchmark.log"
echo "结果目录: $RESULT_DIR" | tee -a "$RESULT_DIR/benchmark.log"

# 自动生成报告
echo "=== 生成测试报告 ===" | tee -a "$RESULT_DIR/benchmark.log"
if command -v python3 >/dev/null 2>&1; then
    python3 generate_report.py "$RESULT_DIR" && echo "HTML报告已生成: $RESULT_DIR/performance_report.html" | tee -a "$RESULT_DIR/benchmark.log"
    python3 generate_markdown_report.py "$RESULT_DIR" && echo "Markdown报告已生成: $RESULT_DIR/performance_report.md" | tee -a "$RESULT_DIR/benchmark.log"
else
    echo "Python3未安装，请手动生成报告：" | tee -a "$RESULT_DIR/benchmark.log"
    echo "python3 generate_report.py $RESULT_DIR" | tee -a "$RESULT_DIR/benchmark.log"
    echo "python3 generate_markdown_report.py $RESULT_DIR" | tee -a "$RESULT_DIR/benchmark.log"
fi
