# Deploying a Dash App on a Unix Server (No sudo + Wheel Deployment)

## Overview

This guide explains how to:

1.  Package a Dash web app as a wheel\
2.  Install it into a **user-owned virtual environment** on a Unix
    server\
3.  Run it on a user port\
4.  Have the admin map `https://unixservername/virdirname` to your app

Because you have **no sudo**, steps involving HTTPS, reverse‑proxying,
or `/virdirname` exposure must be handled by the server admin or by
`.htaccess` (if allowed).

------------------------------------------------------------------------

## 1. Prepare Your Dash App for Wheel Packaging

### Project Structure

    mydashapp/
      src/
        mydashapp/
          __init__.py
          wsgi.py
      pyproject.toml

### `__init__.py`

``` python
from dash import Dash, html

app = Dash(
    __name__,
    routes_pathname_prefix="/virdirname/",
    requests_pathname_prefix="/virdirname/",
)

app.layout = html.Div("Hello from Dash under /virdirname/")

server = app.server
```

### `wsgi.py`

``` python
from . import server
application = server
```

### `pyproject.toml`

``` toml
[build-system]
requires = ["setuptools", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "mydashapp"
version = "0.1.0"
dependencies = [
  "dash",
  "gunicorn"
]

[tool.setuptools]
package-dir = {"" = "src"}

[tool.setuptools.packages.find]
where = ["src"]
```

### Build the wheel

``` bash
python -m pip install --upgrade build
python -m build
```

You get:

    dist/mydashapp-0.1.0-py3-none-any.whl

------------------------------------------------------------------------

## 2. Install Into a User Virtual Environment on the Server

``` bash
mkdir -p ~/apps/mydashapp
cd ~/apps/mydashapp

python3 -m venv venv
source venv/bin/activate

pip install ~/path/to/mydashapp-0.1.0-py3-none-any.whl
```

------------------------------------------------------------------------

## 3. Run the Dash App on a User Port (Gunicorn)

### Manual run

``` bash
cd ~/apps/mydashapp
source venv/bin/activate

gunicorn -b 127.0.0.1:8000 mydashapp.wsgi:application
```

### Background run

``` bash
nohup gunicorn -b 127.0.0.1:8000 mydashapp.wsgi:application > mydashapp.log 2>&1 &
```

This exposes your app at:

    http://127.0.0.1:8000/virdirname/

------------------------------------------------------------------------

## 4. Expose as `https://unixservername/virdirname`

You **cannot** configure this part without sudo.

### What the admin must configure (Nginx example)

``` nginx
location /virdirname/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Script-Name /virdirname;
}
```

### Apache `.htaccess` (only works if allowed)

``` apache
RewriteEngine On
RewriteRule ^virdirname/(.*)$ http://127.0.0.1:8000/virdirname/$1 [P,L]
ProxyPassReverse /virdirname http://127.0.0.1:8000/virdirname
```

------------------------------------------------------------------------

## 5. What You Control vs. What Admin Controls

### You (no sudo)

-   Build wheel\
-   Upload + install wheel\
-   Create venv\
-   Run Dash app with gunicorn\
-   Prepare app for subpath `/virdirname`

### Admin / hosting panel

-   HTTPS termination\
-   Reverse proxy\
-   Exposing `/virdirname`

------------------------------------------------------------------------

If you want, I can also generate: - A zipped folder template\
- A sample runnable Dash app\
- A ready-to-send email to your server admin
