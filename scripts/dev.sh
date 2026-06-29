#!/usr/bin/env zsh
# ─────────────────────────────────────────────────────────────────
#  Guiden — start both servers with one command
#  Usage: ./scripts/dev.sh
# ─────────────────────────────────────────────────────────────────

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# ── Checks ───────────────────────────────────────────────────────
[[ -f venv/bin/activate ]] || {
  echo "✗ No venv found. Run: python3 -m venv venv && pip install -r requirements.txt"
  exit 1
}
[[ -d frontend/node_modules ]] || {
  echo "✗ No node_modules. Run: cd frontend && npm install"
  exit 1
}
[[ -f .env ]] || {
  echo "✗ No .env file. Copy .env.example and fill in your keys."
  exit 1
}

# ── Backend ──────────────────────────────────────────────────────
source venv/bin/activate
uvicorn backend.main:app --reload --port 8000 &
BACKEND=$!
echo "✓ Backend  → http://127.0.0.1:8000  (PID $BACKEND)"

# ── Cleanup on exit ──────────────────────────────────────────────
trap 'echo "\n← Shutting down…"; kill $BACKEND 2>/dev/null; exit 0' INT TERM EXIT

# ── Frontend ─────────────────────────────────────────────────────
source ~/.nvm/nvm.sh 2>/dev/null || true
nvm use 18 --silent 2>/dev/null || true

echo "✓ Frontend → http://localhost:5173"
echo ""
echo "  Press Ctrl+C to stop everything."
echo ""

cd frontend && npm run dev
