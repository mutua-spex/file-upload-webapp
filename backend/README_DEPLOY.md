# Production deployment checklist

This file includes exact commands for provisioning a small production instance using Docker Compose + NGINX + Certbot (Let's Encrypt).

Prerequisites
- A Linux VM (Ubuntu 22.04 recommended) with Docker and Docker Compose installed
- A public domain (e.g., chat.example.com) pointed to this host's IP

1) Copy `.env.example` to `.env` and set `CHATAPP_SECRET_KEY` and `DATABASE_URL`.

```bash
cd /srv/chatapp
cp backend/.env.example .env
# Edit .env and set CHATAPP_SECRET_KEY and DATABASE_URL
```

2) Create `nginx/chatapp.conf` domain replacements and ensure `server_name` is set to your domain.
	- You can set the `DOMAIN` environment variable before starting compose. Example:

```bash
export DOMAIN=chat.example.com
``` 

3) Start services (initial run without certs):

```bash
export CHATAPP_SECRET_KEY="<your-strong-secret>"
sudo docker compose -f docker-compose.prod.yml up -d --build
```

4) Use Certbot to request certificates (webroot method):

```bash
# Run certbot to obtain certs for your domain
sudo docker run --rm -v "${PWD}/certs:/etc/letsencrypt" -v "${PWD}/webroot:/var/www/certbot" certbot/certbot certonly --webroot -w /var/www/certbot -d ${DOMAIN} --email you@example.com --agree-tos --no-eff-email

# After success, reload nginx
sudo docker compose -f docker-compose.prod.yml exec nginx nginx -s reload
```

5) Enable automatic renewal (example cron on host):

```bash
# Edit crontab with `crontab -e` and add:
0 3 * * * docker run --rm -v "/srv/chatapp/certs:/etc/letsencrypt" -v "/srv/chatapp/webroot:/var/www/certbot" certbot/certbot renew --quiet && docker compose -f /srv/chatapp/docker-compose.prod.yml exec nginx nginx -s reload
```

6) Monitoring, logging, and backups
- Logs are written to `backend/logs/chatapp.log` inside container volume `data` or to the host via mounted volumes; configure `logrotate` on the host for the `certs` and `backend/logs` paths as needed.
- Use `scripts/backup_db.ps1` as a simple backup, or create a cron job on host to copy `./backend/chatapp.db` to a backup location.

7) CORS and extra hardening
- Edit `backend/main.py` to set `allow_origins` to the list of allowed clients in production (don't keep `*`).
- Use strong `CHATAPP_SECRET_KEY` and rotate periodically.

If you'd like, I can perform the following next:
- Generate an NGINX config with `server_name` set to your domain and test with Certbot commands.
- Add a `docker-compose` service to automatically run certbot renew.
