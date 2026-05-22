# ccgaming-pos

This repository contains PosIms — a point-of-sale Django project used for demos and small deployments.
## Python Version
python 3.14.3

## Quick start (development)

- Create and activate a virtual environment:

```powershell
python -m venv venv
venv\Scripts\activate
```

- Install dependencies:

```powershell
pip install -r PosIms/requirements.txt
```

- Run migrations and start the dev server:

```powershell
python PosIms/manage.py migrate
python PosIms/manage.py createsuperuser
python PosIms/manage.py runserver
```

## Production deployment

Below are concise, repeatable steps to deploy this project using Nginx + Gunicorn on Linux, and how to achieve the same on a Windows Server using WSL2. There is also a short Windows-native alternative (Waitress + IIS) note.

### Prerequisites (both environments)

- Python 3.8+ installed
- A system user to run the app (Linux) or WSL2 configured on Windows
- Set environment variables for `SECRET_KEY`, `DEBUG=0`, and `ALLOWED_HOSTS` (or use a `.env` loader)
- Use a production-grade database (PostgreSQL recommended) for real deployments — SQLite is okay for testing but not recommended for multi-user production

### Common Django settings to prepare

- In `PosIms/posIms/settings.py` set/ensure:
  - `DEBUG = False` in production
  - read `SECRET_KEY` from environment
  - `ALLOWED_HOSTS = ["your.domain.com"]`
  - set `STATIC_ROOT = BASE_DIR / 'staticfiles'` (or an absolute path)

Run these management commands before finishing the deploy steps:

```bash
python PosIms/manage.py migrate
python PosIms/manage.py collectstatic --noinput
```

### Linux (recommended): Nginx + Gunicorn

1. Create a system user and a project directory; clone the repo and create a virtualenv:

```bash
sudo adduser posuser
sudo mkdir -p /var/www/posims
sudo chown posuser:posuser /var/www/posims
cd /var/www/posims
git clone <repo-url> .
python3 -m venv venv
source venv/bin/activate
pip install -r PosIms/requirements.txt
```

2. Configure environment variables (example using systemd drop-in or an env file). Ensure `SECRET_KEY`, DB settings, and `ALLOWED_HOSTS` are set.

3. Run migrations and collect static files:

```bash
python PosIms/manage.py migrate
python PosIms/manage.py collectstatic --noinput
```

4. Create a systemd service for Gunicorn (file `/etc/systemd/system/posims.service`):

```ini
[Unit]
Description=Gunicorn instance to serve PosIms
After=network.target

[Service]
User=posuser
Group=www-data
WorkingDirectory=/var/www/posims
Environment="PATH=/var/www/posims/venv/bin"
ExecStart=/var/www/posims/venv/bin/gunicorn posIms.wsgi:application \
	--name posims \
	--workers 3 \
	--bind unix:/run/posims.sock

[Install]
WantedBy=multi-user.target
```

Reload systemd and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl start posims
sudo systemctl enable posims
```

5. Configure Nginx to proxy to the Gunicorn socket. Example site file `/etc/nginx/sites-available/posims`:

```nginx
server {
	listen 80;
	server_name your.domain.com;

	location = /favicon.ico { access_log off; log_not_found off; }
	location /static/ {
		alias /var/www/posims/staticfiles/;
	}

	location / {
		include proxy_params;
		proxy_pass http://unix:/run/posims.sock;
	}
}
```

Enable the site and restart Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/posims /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

6. Security & file permissions

- Ensure the `posuser` owns the project files and `www-data` can access the socket and static files. Use `chown`/`chmod` appropriately.
- Use HTTPS (Let’s Encrypt certbot) for production.

### Windows Server: use WSL2 to run Nginx + Gunicorn (recommended)

Windows does not support Gunicorn natively. The simplest approach to use Nginx + Gunicorn on a Windows Server is to install WSL2 (Ubuntu) and follow the Linux steps inside WSL2.

High level:

1. Install WSL2 and Ubuntu from the Microsoft Store.
2. Open the Ubuntu shell and follow the Linux instructions above (clone repo, create virtualenv, install requirements, create systemd-like service using `screen`/`tmux` or convert to a Windows service via tooling, or run under a process manager inside WSL).
3. Optionally expose the WSL2 service to the host and use a Windows-installed Nginx (or run Nginx inside WSL2) to proxy to the Gunicorn socket or port.

Notes:

- Running systemd in WSL can be non-trivial depending on your Windows and WSL versions; newer Windows 11 versions support `systemd` in WSL. If systemd is not available, run Gunicorn via `supervisord`, `tmux`, or a service wrapper.

### Windows-native alternative (no WSL): Waitress + IIS or reverse-proxy

If you must run natively on Windows without WSL, use a Windows WSGI server such as `waitress` and front it with IIS or another reverse proxy. Example quick run with Waitress:

```powershell
pip install waitress
python -m pip install -r PosIms/requirements.txt
python PosIms/manage.py collectstatic --noinput
waitress-serve --port=8000 posIms.wsgi:application
```

Then configure IIS or another Windows reverse-proxy to forward traffic to `http://127.0.0.1:8000` and serve static files from the collected `staticfiles` directory.

### Troubleshooting & next steps

- Check `journalctl -u posims` on Linux for Gunicorn logs
- Check `/var/log/nginx/error.log` for Nginx issues
- Ensure `ALLOWED_HOSTS` includes your domain and that environment variables are correctly loaded

If you want, I can:

- Add example `systemd` and `nginx` config files to a `deploy/` folder
- Create a sample `.env.example` and instructions for environment variable loading

---
Updated deployment instructions for Linux and Windows (WSL2). If you want me to also add deploy scripts or sample config files in the repo, tell me which OS to prioritize.