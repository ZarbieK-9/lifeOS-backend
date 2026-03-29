# lifeOS-backend

Python gRPC API + PostgreSQL. CI/CD: `.github/workflows/ci-cd.yml` — **`pytest`** on `ubuntu-latest`; on **push to `main`**, **`deploy`** runs on a **self-hosted** runner on your server (like pocketbridge): `cd /home/zarbie/lifeos-backend`, `git reset --hard origin/main`, `scripts/deploy.sh` (PM2 via systemd). One-time: `scripts/register-self-hosted-runner.sh` + `svc.sh` (see script header). No SSH secrets required.

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/alembic upgrade head
.venv/bin/python -m app.server
```

Env: `DATABASE_URL`, `JWT_SECRET`, etc. (`app/config.py`). Proto: `./generate.sh`, check stubs: `./check_generated.sh`.
