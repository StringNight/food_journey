#!/bin/bash

# 美食之旅测试运行脚本
# 此脚本用于运行项目的不同类型的测试

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 提示函数
print_header() {
    echo -e "${BLUE}=======================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}=======================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# 确保环境变量设置
export APP_ENV=testing
export TESTING=true
export DATABASE_URL=sqlite+aiosqlite:///:memory:
export RATE_LIMIT_TEST_MODE=true
export MAX_LOGIN_ATTEMPTS=5

# 创建测试结果目录
mkdir -p test_results
mkdir -p performance_reports

# 运行所有基础测试
run_basic_tests() {
    print_header "运行基础功能测试"
    pytest tests/test_auth.py tests/test_recipes.py tests/test_favorites.py tests/test_chat.py tests/test_workout.py -v
    
    if [ $? -eq 0 ]; then
        print_success "基础功能测试通过"
    else
        print_error "基础功能测试失败"
        exit 1
    fi
}

# 运行集成测试
run_integration_tests() {
    print_header "运行集成测试"
    pytest tests/test_comprehensive.py tests/test_frontend_integration.py -v
    
    if [ $? -eq 0 ]; then
        print_success "集成测试通过"
    else
        print_error "集成测试失败"
        exit 1
    fi
}

# 运行性能测试
run_performance_tests() {
    print_header "运行性能测试"
    print_warning "性能测试可能需要较长时间，请耐心等待..."
    pytest tests/test_performance.py -v
    
    if [ $? -eq 0 ]; then
        print_success "性能测试通过"
        echo "性能测试报告已生成在 performance_reports 目录中"
    else
        print_error "性能测试失败或性能不达标"
    fi
}

# 运行所有测试
run_all_tests() {
    print_header "运行所有测试"
    pytest
    
    if [ $? -eq 0 ]; then
        print_success "所有测试通过"
    else
        print_error "测试失败"
        exit 1
    fi
}

# 使用指定并发数运行测试
run_parallel_tests() {
    num_workers=$1
    print_header "并行运行测试（$num_workers 个工作进程）"
    pytest -xvs -n $num_workers
    
    if [ $? -eq 0 ]; then
        print_success "并行测试通过"
    else
        print_error "并行测试失败"
        exit 1
    fi
}

# 运行带覆盖率的测试
run_coverage_tests() {
    print_header "运行带覆盖率的测试"
    pytest --cov=src --cov-report=html --cov-report=term
    
    if [ $? -eq 0 ]; then
        print_success "覆盖率测试通过"
        echo "覆盖率报告已生成在 htmlcov 目录中"
    else
        print_error "覆盖率测试失败"
        exit 1
    fi
}

# 显示帮助信息
show_help() {
    echo "美食之旅测试运行脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --all           运行所有测试"
    echo "  --basic         只运行基础功能测试"
    echo "  --integration   只运行集成测试"
    echo "  --performance   只运行性能测试"
    echo "  --parallel N    使用N个工作进程并行运行测试"
    echo "  --coverage      运行带覆盖率的测试"
    echo "  --help          显示此帮助信息"
    echo ""
}

# 主函数
main() {
    if [ $# -eq 0 ]; then
        show_help
        exit 0
    fi
    
    case "$1" in
        --all)
            run_all_tests
            ;;
        --basic)
            run_basic_tests
            ;;
        --integration)
            run_integration_tests
            ;;
        --performance)
            run_performance_tests
            ;;
        --parallel)
            if [ -z "$2" ]; then
                print_error "请指定并发数"
                exit 1
            fi
            run_parallel_tests $2
            ;;
        --coverage)
            run_coverage_tests
            ;;
        --help)
            show_help
            ;;
        *)
            print_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@" 