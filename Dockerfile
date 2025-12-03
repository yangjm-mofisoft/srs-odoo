# Use Python 3.12 (Standard for Odoo 18/19+) based on Debian Bookworm
FROM python:3.12-slim-bookworm

# 1. Install System Dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    python3-dev \
    libldap2-dev \
    libsasl2-dev \
    postgresql-client \
    libpq-dev \
    libxml2-dev \
    libxslt1-dev \
    libjpeg-dev \
    zlib1g-dev \
    curl \
    gnupg2 \
    ca-certificates \
    adduser \
    && rm -rf /var/lib/apt/lists/*

# 2. Create Odoo user and directories FIRST
# We create the user early so we can assign permissions before filling folders
# This prevents the "useradd warning" and the slow "chown" step later
RUN useradd -m -d /var/lib/odoo -s /bin/bash odoo && \
    mkdir -p /etc/odoo /mnt/extra-addons /var/lib/odoo /opt/odoo && \
    chown -R odoo:odoo /opt/odoo /etc/odoo /mnt/extra-addons /var/lib/odoo

# 3. Switch to Odoo user for cloning
# By cloning AS the user, files are automatically owned by 'odoo'.
# No massive 'chown' needed later!
USER odoo
WORKDIR /opt/odoo

RUN git clone --depth 1 --branch master https://github.com/odoo/odoo.git .

# 4. Switch back to Root to install Python packages
# pip needs root access to install global packages
USER root
RUN pip3 install --upgrade pip && \
    pip3 install --no-cache-dir -r requirements.txt

# 5. Switch back to Odoo user for runtime
USER odoo

# 6. Define Entrypoint
ENTRYPOINT ["python3", "/opt/odoo/odoo-bin"]
CMD ["-c", "/etc/odoo/odoo.conf"]