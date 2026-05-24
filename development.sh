#!/bin/bash

# Colors for terminal styling
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
RESET='\033[0m'

# Core Directories
CWD="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LOG_DIR="$CWD/logs"
PID_DIR="$CWD/.pids"

mkdir -p "$LOG_DIR"
mkdir -p "$PID_DIR"

# Executable Paths
VENV_PYTHON="$CWD/venv/bin/python"
VENV_UVICORN="$CWD/venv/bin/uvicorn"
VENV_CELERY="$CWD/venv/bin/celery"
VENV_ALEMBIC="$CWD/venv/bin/alembic"

# Fallback to system executables if virtual environment is not configured
if [ ! -f "$VENV_PYTHON" ]; then
  echo -e "${YELLOW}⚠️  Virtual environment 'venv' not found. Using system python/celery/uvicorn...${RESET}"
  VENV_PYTHON="python3"
  VENV_UVICORN="uvicorn"
  VENV_CELERY="celery"
  VENV_ALEMBIC="alembic"
fi

# Detect docker compose version
get_docker_compose_cmd() {
  if docker compose version >/dev/null 2>&1; then
    echo "docker compose"
  elif docker-compose version >/dev/null 2>&1; then
    echo "docker-compose"
  else
    echo ""
  fi
}

DOCKER_COMPOSE_CMD=$(get_docker_compose_cmd)

# Helper: Check if a process is running
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

# Action: Start development services
run_services() {
  echo -e "${BLUE}🌱 Starting RAGaaS Local Development Environment...${RESET}"

  # 1. Start Docker dependencies
  if [ -z "$DOCKER_COMPOSE_CMD" ]; then
    echo -e "${RED}❌ Docker / Docker Compose not found. Please install Docker to run Postgres, Redis, and Qdrant.${RESET}"
    exit 1
  fi

  echo -e "${CYAN}[*] Starting database, cache, and vector store (Postgres, Redis, Qdrant)...${RESET}"
  $DOCKER_COMPOSE_CMD up -d postgres redis qdrant
  if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠️  Failed to start Docker services. Continuing with local processes (make sure Postgres, Redis, and Qdrant are running)...${RESET}"
  fi

  # Wait for services to initialize
  echo -e "${CYAN}[*] Waiting for databases to become healthy...${RESET}"
  sleep 4

  # 2. Run Database Migrations
  echo -e "${CYAN}[*] Applying database migrations...${RESET}"
  $VENV_ALEMBIC upgrade head > "$LOG_DIR/migrations.log" 2>&1
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}   ✓ Database migrated.${RESET}"
  else
    echo -e "${YELLOW}   ⚠️  Migration failed or skipped (check logs/migrations.log for details).${RESET}"
  fi

  # 3. Seed Database
  echo -e "${CYAN}[*] Seeding database with test tenant and API key...${RESET}"
  $VENV_PYTHON -m scripts.seed > "$LOG_DIR/seed.log" 2>&1
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}   ✓ Seed complete. Checked/Created test tenant.${RESET}"
    # Print the seeded API key if newly created
    grep -A 5 "YOUR API KEY" "$LOG_DIR/seed.log" | sed 's/^/     /'
  else
    echo -e "${YELLOW}   ⚠️  Seed task encountered issues (check logs/seed.log).${RESET}"
  fi

  # 4. Start FastAPI Backend
  if is_running "$PID_DIR/fastapi.pid"; then
    echo -e "${YELLOW}⚠️  FastAPI is already running (PID: $(cat "$PID_DIR/fastapi.pid")).${RESET}"
  else
    echo -e "${CYAN}[*] Starting FastAPI (api.main)...${RESET}"
    $VENV_UVICORN api.main:app --host 0.0.0.0 --port 8000 --reload > "$LOG_DIR/fastapi.log" 2>&1 &
    echo $! > "$PID_DIR/fastapi.pid"
    echo -e "${GREEN}   ✓ FastAPI running in background.${RESET}"
  fi

  # 5. Start Celery Worker
  if is_running "$PID_DIR/celery.pid"; then
    echo -e "${YELLOW}⚠️  Celery worker is already running (PID: $(cat "$PID_DIR/celery.pid")).${RESET}"
  else
    echo -e "${CYAN}[*] Starting Celery worker...${RESET}"
    $VENV_CELERY -A workers.celery_app worker --loglevel=info > "$LOG_DIR/celery.log" 2>&1 &
    echo $! > "$PID_DIR/celery.pid"
    echo -e "${GREEN}   ✓ Celery worker running in background.${RESET}"
  fi

  # 6. Start Frontend Web Server (Port 5000)
  if is_running "$PID_DIR/frontend.pid"; then
    echo -e "${YELLOW}⚠️  Frontend server is already running (PID: $(cat "$PID_DIR/frontend.pid")).${RESET}"
  else
    echo -e "${CYAN}[*] Starting Frontend server on port 5000...${RESET}"
    $VENV_PYTHON -m http.server 5000 --directory "$CWD/frontend" > "$LOG_DIR/frontend.log" 2>&1 &
    echo $! > "$PID_DIR/frontend.pid"
    echo -e "${GREEN}   ✓ Frontend static server running in background.${RESET}"
  fi

  echo -e "\n${GREEN}🚀 RAGaaS environment is ready!${RESET}"
  echo -e "   - Frontend Console:   ${BLUE}http://localhost:5000${RESET}"
  echo -e "   - FastAPI Gateway:    ${BLUE}http://localhost:8000${RESET}"
  echo -e "   - FastAPI Swagger:    ${BLUE}http://localhost:8000/docs${RESET}"
  echo -e "   - Qdrant Dashboard:   ${BLUE}http://localhost:6333/dashboard${RESET}"
  echo -e "\n   To view logs, run:    ${CYAN}./dev.sh logs [fastapi|celery|frontend]${RESET}"
  echo -e "   To stop services, run: ${CYAN}./dev.sh stop${RESET}\n"
}

# Action: Stop services
stop_services() {
  echo -e "${BLUE}🛑 Stopping RAGaaS Local Development Environment...${RESET}"

  # Stop Frontend
  if is_running "$PID_DIR/frontend.pid"; then
    local pid=$(cat "$PID_DIR/frontend.pid")
    echo -e "${CYAN}[*] Stopping Frontend server (PID: $pid)...${RESET}"
    kill "$pid" && rm -f "$PID_DIR/frontend.pid"
  else
    echo -e "${YELLOW}   Frontend server not running.${RESET}"
  fi

  # Stop Celery Worker
  if is_running "$PID_DIR/celery.pid"; then
    local pid=$(cat "$PID_DIR/celery.pid")
    echo -e "${CYAN}[*] Stopping Celery worker (PID: $pid)...${RESET}"
    kill "$pid" && rm -f "$PID_DIR/celery.pid"
  else
    echo -e "${YELLOW}   Celery worker not running.${RESET}"
  fi

  # Stop FastAPI
  if is_running "$PID_DIR/fastapi.pid"; then
    local pid=$(cat "$PID_DIR/fastapi.pid")
    echo -e "${CYAN}[*] Stopping FastAPI backend (PID: $pid)...${RESET}"
    kill "$pid" && rm -f "$PID_DIR/fastapi.pid"
  else
    echo -e "${YELLOW}   FastAPI backend not running.${RESET}"
  fi

  # Stop Docker containers
  if [ -n "$DOCKER_COMPOSE_CMD" ]; then
    echo -e "${CYAN}[*] Stopping Docker services (Postgres, Redis, Qdrant)...${RESET}"
    $DOCKER_COMPOSE_CMD stop
  fi

  echo -e "${GREEN}✓ All services stopped.${RESET}"
}

# Action: View logs
view_logs() {
  local service="$1"
  case "$service" in
    fastapi|api)
      echo -e "${BLUE}📋 Tailing FastAPI backend logs (logs/fastapi.log):${RESET}"
      tail -n 50 -f "$LOG_DIR/fastapi.log"
      ;;
    celery|worker)
      echo -e "${BLUE}📋 Tailing Celery worker logs (logs/celery.log):${RESET}"
      tail -n 50 -f "$LOG_DIR/celery.log"
      ;;
    frontend|front)
      echo -e "${BLUE}📋 Tailing Frontend server logs (logs/frontend.log):${RESET}"
      tail -n 50 -f "$LOG_DIR/frontend.log"
      ;;
    postgres|db)
      if [ -n "$DOCKER_COMPOSE_CMD" ]; then
        $DOCKER_COMPOSE_CMD logs -f postgres
      else
        echo -e "${RED}Docker compose not available.${RESET}"
      fi
      ;;
    redis|cache)
      if [ -n "$DOCKER_COMPOSE_CMD" ]; then
        $DOCKER_COMPOSE_CMD logs -f redis
      else
        echo -e "${RED}Docker compose not available.${RESET}"
      fi
      ;;
    qdrant|vector)
      if [ -n "$DOCKER_COMPOSE_CMD" ]; then
        $DOCKER_COMPOSE_CMD logs -f qdrant
      else
        echo -e "${RED}Docker compose not available.${RESET}"
      fi
      ;;
    *)
      echo -e "${RED}❌ Unknown service: '$service'. Available options: [fastapi|celery|frontend|postgres|redis|qdrant]${RESET}"
      exit 1
      ;;
  esac
}

# Parse command line argument
COMMAND="$1"
shift

case "$COMMAND" in
  run|start)
    run_services
    ;;
  stop)
    stop_services
    ;;
  logs)
    if [ -z "$1" ]; then
      echo -e "${RED}❌ Please specify a service to tail logs. Example: ./dev.sh logs fastapi${RESET}"
      echo -e "   Valid services: [fastapi|celery|frontend|postgres|redis|qdrant]"
      exit 1
    fi
    view_logs "$1"
    ;;
  status)
    echo -e "${BLUE}📊 Service Status:${RESET}"
    is_running "$PID_DIR/fastapi.pid" && echo -e "   - FastAPI:    ${GREEN}RUNNING (PID: $(cat "$PID_DIR/fastapi.pid"))${RESET}" || echo -e "   - FastAPI:    ${RED}STOPPED${RESET}"
    is_running "$PID_DIR/celery.pid" && echo -e "   - Celery:     ${GREEN}RUNNING (PID: $(cat "$PID_DIR/celery.pid"))${RESET}" || echo -e "   - Celery:     ${RED}STOPPED${RESET}"
    is_running "$PID_DIR/frontend.pid" && echo -e "   - Frontend:   ${GREEN}RUNNING (PID: $(cat "$PID_DIR/frontend.pid"))${RESET}" || echo -e "   - Frontend:   ${RED}STOPPED${RESET}"
    if [ -n "$DOCKER_COMPOSE_CMD" ]; then
      echo -e "\n   Docker status:"
      $DOCKER_COMPOSE_CMD ps
    fi
    ;;
  *)
    echo -e "${YELLOW}Usage: ./dev.sh {run|stop|logs|status}${RESET}"
    echo -e "   - ${CYAN}run${RESET}     : Starts postgres, redis, qdrant, fastapi, celery, and frontend"
    echo -e "   - ${CYAN}stop${RESET}    : Stops all background processes and docker services"
    echo -e "   - ${CYAN}logs [s]${RESET}: Tails logs for the specified service [fastapi|celery|frontend|postgres|redis|qdrant]"
    echo -e "   - ${CYAN}status${RESET}  : Checks what processes are currently running"
    exit 1
    ;;
esac
