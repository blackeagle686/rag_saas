#!/bin/bash

# Colors for terminal styling
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
RESET='\033[0m'

CWD="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LOG_DIR="$CWD/logs"
PID_DIR="$CWD/.pids"

mkdir -p "$LOG_DIR"
mkdir -p "$PID_DIR"

VENV_PYTHON="$CWD/venv/bin/python"
VENV_CELERY="$CWD/venv/bin/celery"

if [ ! -f "$VENV_PYTHON" ]; then
  VENV_PYTHON="python3"
  VENV_CELERY="celery"
fi

is_running() {
  local pid_file="$1"
  if [ -f "$pid_file" ]; then
    local pid=$(cat "$pid_file")
    if ps -p "$pid" > /dev/null 2>&1; then
      return 0 # running
    fi
  fi
  return 1 # not running
}

start_services() {
    echo -e "${BLUE}🌱 Starting RAGaaS Local Services (No Docker)...${RESET}"

    # 1. Start Redis
    if is_running "$PID_DIR/redis.pid"; then
        echo -e "${YELLOW}⚠️  Redis is already running.${RESET}"
    else
        echo -e "${CYAN}[*] Starting Redis...${RESET}"
        redis-server --port 6380 --daemonize yes --logfile "$LOG_DIR/redis.log" --pidfile "$PID_DIR/redis.pid"
        if [ $? -eq 0 ]; then
             echo -e "${GREEN}   ✓ Redis started.${RESET}"
        else
             echo -e "${RED}   ❌ Failed to start Redis. Make sure redis-server is installed locally.${RESET}"
        fi
    fi

    sleep 1

    # Configure Django & Celery to use the new Redis port
    export REDIS_URL="redis://localhost:6380/0"
    export CELERY_BROKER_URL="redis://localhost:6380/1"
    export CELERY_RESULT_BACKEND="redis://localhost:6380/2"

    # 2. Start Django Backend
    if is_running "$PID_DIR/django.pid"; then
        echo -e "${YELLOW}⚠️  Django is already running.${RESET}"
    else
        echo -e "${CYAN}[*] Starting Django backend...${RESET}"
        $VENV_PYTHON manage.py runserver 0.0.0.0:8000 > "$LOG_DIR/django.log" 2>&1 &
        echo $! > "$PID_DIR/django.pid"
        echo -e "${GREEN}   ✓ Django started.${RESET}"
    fi

    # 3. Start Celery Worker
    if is_running "$PID_DIR/celery.pid"; then
        echo -e "${YELLOW}⚠️  Celery worker is already running.${RESET}"
    else
        echo -e "${CYAN}[*] Starting Celery worker...${RESET}"
        $VENV_CELERY -A config worker -Q celery,realtime,bulk_ingestion --loglevel=info > "$LOG_DIR/celery.log" 2>&1 &
        echo $! > "$PID_DIR/celery.pid"
        echo -e "${GREEN}   ✓ Celery worker started.${RESET}"
    fi

    # 4. Start Frontend
    if is_running "$PID_DIR/frontend.pid"; then
        echo -e "${YELLOW}⚠️  Frontend is already running.${RESET}"
    else
        echo -e "${CYAN}[*] Starting React Frontend...${RESET}"
        cd "$CWD/frontend" && npm run dev -- --port 5000 > "$LOG_DIR/frontend.log" 2>&1 &
        echo $! > "$PID_DIR/frontend.pid"
        echo -e "${GREEN}   ✓ Frontend started.${RESET}"
    fi

    echo -e "\n${GREEN}🚀 All local services are running!${RESET}"
    echo -e "   - Frontend: http://localhost:5000"
    echo -e "   - Backend:  http://localhost:8000"
    echo -e "   Logs: tail -f logs/*.log"
}

stop_services() {
    echo -e "${BLUE}🛑 Stopping Local Services...${RESET}"
    
    for service in frontend celery django redis; do
        if is_running "$PID_DIR/$service.pid"; then
            pid=$(cat "$PID_DIR/$service.pid")
            echo -e "${CYAN}[*] Stopping $service (PID: $pid)...${RESET}"
            kill "$pid"
            rm -f "$PID_DIR/$service.pid"
        fi
    done
    
    echo -e "${GREEN}✓ All services stopped.${RESET}"
}

tail_logs() {
    local service="$1"
    if [ -z "$service" ]; then
        echo -e "${BLUE}📋 Tailing all logs...${RESET}"
        tail -f "$LOG_DIR"/django.log "$LOG_DIR"/celery.log "$LOG_DIR"/frontend.log "$LOG_DIR"/redis.log
    else
        tail -f "$LOG_DIR/$service.log"
    fi
}

case "$1" in
    start|run)
        start_services
        ;;
    stop)
        stop_services
        ;;
    logs)
        tail_logs "$2"
        ;;
    *)
        echo -e "${YELLOW}Usage: ./run_dev.sh {start|stop|logs [service]}${RESET}"
        exit 1
        ;;
esac
