# lifeOS-backend

Python gRPC API + PostgreSQL. CI/CD: `.github/workflows/ci-cd.yml` — `pytest` on GitHub-hosted runners; on **push to `main`**, SSH to your server, `cd /home/zarbie/lifeos-backend`, and run `scripts/deploy.sh`. Set repo secrets `DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_SSH_KEY`. Optional `DEPLOY_SSH_PORT` if SSH is not on 22. Use **public IPv4** DNS or IP for `DEPLOY_HOST`; workflow uses **`ssh -4`**. Deploy needs **inbound TCP** to your router → server (forward to `sshd`); timeout usually means no forward, firewall, wrong IP, or **CGNAT** (no public IPv4—use a tunnel or self-hosted runner).

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/alembic upgrade head
.venv/bin/python -m app.server
```

Env: `DATABASE_URL`, `JWT_SECRET`, etc. (`app/config.py`). Proto: `./generate.sh`, check stubs: `./check_generated.sh`.
