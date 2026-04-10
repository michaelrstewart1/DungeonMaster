#!/usr/bin/env bash
# Provisioning script for the DungeonMaster VM (Ubuntu 24.04 + AMD ROCm GPU)
# Run as root or with sudo after fresh Ubuntu 24.04 install.
#
# Usage: sudo bash provision.sh

set -euo pipefail

echo "═══════════════════════════════════════"
echo "  AI Dungeon Master — VM Provisioning"
echo "═══════════════════════════════════════"

# --- System updates ---
echo "[1/6] Updating system packages..."
apt-get update -qq && apt-get upgrade -y -qq

# --- Docker ---
echo "[2/6] Installing Docker..."
if ! command -v docker &>/dev/null; then
  curl -fsSL https://get.docker.com | sh
  systemctl enable --now docker
else
  echo "  Docker already installed: $(docker --version)"
fi

# Add the default non-root user to docker group
DEFAULT_USER=$(getent passwd 1000 | cut -d: -f1 || true)
if [ -n "$DEFAULT_USER" ]; then
  usermod -aG docker "$DEFAULT_USER"
  echo "  Added $DEFAULT_USER to docker group"
fi

# --- AMD GPU / ROCm userspace ---
echo "[3/6] Setting up AMD GPU support..."

apt-get install -y -qq linux-firmware mesa-utils

if lspci | grep -qi "navi"; then
  echo "  ✓ AMD Navi GPU detected"
  lspci | grep -i vga
else
  echo "  ⚠ No AMD Navi GPU detected — ROCm may not work"
fi

# Ensure render and video groups exist and add user
if [ -n "$DEFAULT_USER" ]; then
  usermod -aG video,render "$DEFAULT_USER" 2>/dev/null || true
fi

if [ -e /dev/kfd ]; then
  echo "  ✓ /dev/kfd available"
else
  echo "  ⚠ /dev/kfd not found — GPU compute may not work in containers"
fi

# --- Git + Clone repo ---
echo "[4/6] Cloning DungeonMaster repository..."
apt-get install -y -qq git

DEPLOY_DIR="/opt/dungeon-master"
if [ ! -d "$DEPLOY_DIR" ]; then
  git clone https://github.com/michaelrstewart1/DungeonMaster.git "$DEPLOY_DIR"
else
  echo "  Already cloned, pulling latest..."
  cd "$DEPLOY_DIR" && git pull
fi

# --- Environment config ---
echo "[5/6] Setting up environment..."
cd "$DEPLOY_DIR"
if [ ! -f .env ]; then
  cp .env.example .env
  sed -i 's/POSTGRES_PASSWORD=changeme/POSTGRES_PASSWORD='"$(openssl rand -hex 16)"'/' .env
  echo "  ✓ .env created with random DB password"
else
  echo "  .env already exists, skipping"
fi

if [ -n "$DEFAULT_USER" ]; then
  chown -R "$DEFAULT_USER:$DEFAULT_USER" "$DEPLOY_DIR"
fi

# --- Launch stack ---
echo "[6/6] Starting Docker Compose stack with GPU..."
cd "$DEPLOY_DIR"
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d --build

# Pull Ollama model in the background
echo ""
echo "Pulling LLM model (llama3.1:8b) — this may take a few minutes..."
docker compose exec -T ollama ollama pull llama3.1:8b &

echo ""
echo "═══════════════════════════════════════"
echo "  ✓ Provisioning complete!"
echo "═══════════════════════════════════════"
echo ""
echo "  Frontend: http://$(hostname -I | awk '{print $1}'):3000"
echo "  Backend:  http://$(hostname -I | awk '{print $1}'):8000"
echo "  Ollama:   http://$(hostname -I | awk '{print $1}'):11434"
echo ""
echo "  Logs: cd $DEPLOY_DIR && docker compose logs -f"
echo "  Stop: cd $DEPLOY_DIR && docker compose down"
echo ""
