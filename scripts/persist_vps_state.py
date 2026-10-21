import sys
import paramiko

sys.stdout.reconfigure(encoding='utf-8')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('169.58.230.132', username='root', password='4722ADwTjGA')

cmd = """
echo "=== 1. SERVICIOS SYSTEMD ==="
systemctl is-active openmausbot traidinghub traidinghub-bot traidinghub-incubator

echo "=== 2. MEMORIA Y DISCO ==="
free -h
df -h /

echo "=== 3. PYTHON GLOBAL WRAPPERS & QUANT STACK ==="
which python3 python pip
python3 -c "import vectorbt, ccxt, pandas, scipy, hyperliquid, telegram, yaml; print('Full Quant Stack: OK')"

echo "=== 4. COPIAS DE SEGURIDAD OPENMAUSBOT ==="
cp -p /root/.openmausbot/bots.json /root/.openmausbot/bots.json.backup_$(date +%Y%m%d_%H%M%S)
cp -p /root/.openmausbot/sessions.json /root/.openmausbot/sessions.json.backup_$(date +%Y%m%d_%H%M%S)
ls -la /root/.openmausbot/bots.json* /root/.openmausbot/sessions.json*

echo "=== 5. INICIALIZAR Y PERSISTIR GIT EN /root/AlgrokQuant ==="
cd /root/AlgrokQuant
cat << 'EOF' > .gitignore
venv/
*.pyc
__pycache__/
logs/*.log
.env
data/raw/*
EOF

if [ ! -d .git ]; then
    git init
    git config user.name "Nexus"
    git config user.email "nexus@algrokquant.local"
fi
git add -A
git commit -m "chore(algrokquant): snapshot y persistencia total de la infraestructura, libreria obsidian y configuraciones" || echo "Git: sin cambios adicionales"
git status -s

echo "=== 6. RESUMEN DE FICHEROS EN ALGROKQUANT ==="
find . -maxdepth 3 -not -path '*/.*' -not -path './venv*' | sort
"""
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode('utf-8', errors='replace'))
print("ERR:", stderr.read().decode('utf-8', errors='replace'))
ssh.close()
