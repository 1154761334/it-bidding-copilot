#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$ROOT_DIR/logs"
RUN_DIR="$ROOT_DIR/.run"
BACKEND_PID_FILE="$RUN_DIR/backend.pid"
FRONTEND_PID_FILE="$RUN_DIR/frontend.pid"
BACKEND_LOG_FILE="$LOG_DIR/backend.log"
FRONTEND_LOG_FILE="$LOG_DIR/frontend.log"

mkdir -p "$LOG_DIR" "$RUN_DIR"

resolve_python() {
    if [ -x "$ROOT_DIR/venv/bin/python" ]; then
        echo "$ROOT_DIR/venv/bin/python"
        return
    fi

    if command -v python3 >/dev/null 2>&1; then
        command -v python3
        return
    fi

    if command -v python >/dev/null 2>&1; then
        command -v python
        return
    fi

    echo "No Python interpreter found. Install python3 or create ./venv first." >&2
    exit 1
}

ensure_env() {
    if [ ! -f "$ROOT_DIR/.env" ]; then
        echo ".env not found. Copying from .env.example ..."
        cp "$ROOT_DIR/.env.example" "$ROOT_DIR/.env"
        echo "Edit .env and re-run the script."
        exit 1
    fi
}

is_pid_running() {
    local pid="$1"
    if [ -z "$pid" ]; then
        return 1
    fi
    kill -0 "$pid" >/dev/null 2>&1
}

cleanup_pid_file() {
    local pid_file="$1"
    if [ -f "$pid_file" ]; then
        local pid
        pid="$(cat "$pid_file" 2>/dev/null || true)"
        if ! is_pid_running "$pid"; then
            rm -f "$pid_file"
        fi
    fi
}

start_database() {
    if command -v docker >/dev/null 2>&1; then
        echo "Starting PostgreSQL/pgvector via docker compose ..."
        (cd "$ROOT_DIR" && docker compose up -d pgvector >/dev/null)
    else
        echo "Docker not found. Ensure PostgreSQL is already running."
    fi
}

start_backend() {
    cleanup_pid_file "$BACKEND_PID_FILE"
    if [ -f "$BACKEND_PID_FILE" ]; then
        echo "Backend already running with PID $(cat "$BACKEND_PID_FILE")."
        return
    fi

    echo "Starting FastAPI backend on :8000 ..."
    local python_bin
    python_bin="$(resolve_python)"
    cd "$ROOT_DIR"
    nohup "$python_bin" -m uvicorn main:app --host 0.0.0.0 --port 8000 >"$BACKEND_LOG_FILE" 2>&1 &
    echo $! >"$BACKEND_PID_FILE"
}

start_frontend() {
    cleanup_pid_file "$FRONTEND_PID_FILE"
    if [ -f "$FRONTEND_PID_FILE" ]; then
        echo "Frontend already running with PID $(cat "$FRONTEND_PID_FILE")."
        return
    fi

    echo "Starting Vite frontend on :20031 ..."
    cd "$ROOT_DIR/frontend"
    nohup npm run dev -- --host 0.0.0.0 >"$FRONTEND_LOG_FILE" 2>&1 &
    echo $! >"$FRONTEND_PID_FILE"
}

stop_service() {
    local pid_file="$1"
    local label="$2"

    cleanup_pid_file "$pid_file"
    if [ ! -f "$pid_file" ]; then
        echo "$label is not running."
        return
    fi

    local pid
    pid="$(cat "$pid_file")"
    echo "Stopping $label (PID $pid) ..."
    kill "$pid" >/dev/null 2>&1 || true

    for _ in $(seq 1 10); do
        if ! is_pid_running "$pid"; then
            rm -f "$pid_file"
            echo "$label stopped."
            return
        fi
        sleep 1
    done

    echo "$label did not stop gracefully; sending SIGKILL."
    kill -9 "$pid" >/dev/null 2>&1 || true
    rm -f "$pid_file"
}

show_status() {
    cleanup_pid_file "$BACKEND_PID_FILE"
    cleanup_pid_file "$FRONTEND_PID_FILE"

    if [ -f "$BACKEND_PID_FILE" ]; then
        echo "Backend: running (PID $(cat "$BACKEND_PID_FILE"))"
    else
        echo "Backend: stopped"
    fi

    if [ -f "$FRONTEND_PID_FILE" ]; then
        echo "Frontend: running (PID $(cat "$FRONTEND_PID_FILE"))"
    else
        echo "Frontend: stopped"
    fi

    echo "Backend log: $BACKEND_LOG_FILE"
    echo "Frontend log: $FRONTEND_LOG_FILE"
}

start_all() {
    ensure_env
    start_database
    start_backend
    start_frontend
    echo "Startup complete."
    echo "Frontend: http://localhost:20031"
    echo "API: http://localhost:8000"
    echo "Health: http://localhost:8000/healthz"
}

stop_all() {
    stop_service "$FRONTEND_PID_FILE" "Frontend"
    stop_service "$BACKEND_PID_FILE" "Backend"
}

COMMAND="${1:-start}"

case "$COMMAND" in
    start)
        start_all
        ;;
    stop)
        stop_all
        ;;
    restart)
        stop_all
        start_all
        ;;
    status)
        show_status
        ;;
    *)
        echo "Usage: ./start_app.sh {start|stop|restart|status}"
        exit 1
        ;;
esac
