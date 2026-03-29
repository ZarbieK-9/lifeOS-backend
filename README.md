# lifeOS-backend

Python gRPC API + PostgreSQL. CI/CD: `.github/workflows/ci-cd.yml` — `pytest` on GitHub-hosted runners; on **push to `main`**, SSH to your server, `cd /home/zarbie/lifeos-backend`, and run `scripts/deploy.sh`. Set repo secrets `DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_SSH_KEY`.

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/alembic upgrade head
.venv/bin/python -m app.server
```

Env: `DATABASE_URL`, `JWT_SECRET`, etc. (`app/config.py`). Proto: `./generate.sh`, check stubs: `./check_generated.sh`.
