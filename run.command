#!/bin/zsh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

ensure_python() {
  if command -v python3 >/dev/null 2>&1; then
    return 0
  fi

  echo ""
  echo "未找到 python3。"
  echo "这台设备暂时不能直接运行当前项目。"
  echo "如需完全免安装运行，需要提前打包成独立应用。"
  exit 1
}

ensure_venv() {
  if [ ! -d ".venv" ]; then
    echo ""
    echo "正在创建运行环境..."
    python3 -m venv .venv
  fi

  source ".venv/bin/activate"

  echo ""
  echo "正在检查依赖..."
  pip install -q requests beautifulsoup4
}

run_search() {
  echo ""
  read "query?请输入搜索关键词: "
  read "limit?请输入结果数量（默认 20）: "
  if [ -z "$limit" ]; then
    limit="20"
  fi
  python3 skills/company-filter-refresh/refresh.py search --query "$query" --limit "$limit"
}

run_discover() {
  echo ""
  read "company?请输入公司名（可模糊匹配，留空表示全部）: "
  if [ -n "$company" ]; then
    python3 skills/company-filter-refresh/refresh.py discover --company "$company"
  else
    python3 skills/company-filter-refresh/refresh.py discover
  fi
}

run_email() {
  echo ""
  read "company?请输入公司名（可模糊匹配，留空表示全部）: "
  if [ -n "$company" ]; then
    python3 skills/company-filter-refresh/refresh.py email --company "$company"
  else
    python3 skills/company-filter-refresh/refresh.py email
  fi
}

run_enrich() {
  echo ""
  read "company?请输入公司名（可模糊匹配，留空表示全部）: "
  if [ -n "$company" ]; then
    python3 skills/company-filter-refresh/refresh.py enrich --company "$company"
  else
    python3 skills/company-filter-refresh/refresh.py enrich
  fi
}

run_status() {
  python3 skills/company-filter-refresh/refresh.py status
}

main_menu() {
  echo ""
  echo "========================================"
  echo "Charlie Skill 一键运行"
  echo "========================================"
  echo "1) 搜索公司"
  echo "2) 抓取高管"
  echo "3) 生成邮箱"
  echo "4) 补充联系方式"
  echo "5) 查看数据状态"
  echo "0) 退出"
  echo ""
  read "choice?请输入数字: "

  case "$choice" in
    1) run_search ;;
    2) run_discover ;;
    3) run_email ;;
    4) run_enrich ;;
    5) run_status ;;
    0) exit 0 ;;
    *)
      echo ""
      echo "输入无效，请重新运行。"
      exit 1
      ;;
  esac
}

ensure_python
ensure_venv
main_menu

echo ""
echo "运行结束。按回车关闭窗口。"
read
