# Use Python 3.12 (Standard for Odoo 18/19+) based on Debian Bookworm
FROM python:3.12-slim-bookworm

# 1. Install System Dependencies
# specific libraries required for Odoo (Postgres client, LDAP, XML/XSLT, etc.)
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

# 2. Create Odoo user and directory
WORKDIR /opt/odoo

# 3. Clone Odoo Source Code (Master Branch = Odoo 19)
# --depth 1 makes the download faster (only latest commit)
RUN git clone --depth 1 --branch master https://github.com/odoo/odoo.git .

# 4. Install Odoo Python Requirements
RUN pip3 install --upgrade pip && \
    pip3 install --no-cache-dir -r requirements.txt

# 5. Create specific directories for config and addons
RUN mkdir -p /etc/odoo /mnt/extra-addons /var/lib/odoo

# 6. Set permissions
# We create a user 'odoo' to run the application securely
RUN useradd -m -d /var/lib/odoo -s /bin/bash odoo && \
    chown -R odoo:odoo /opt/odoo /etc/odoo /mnt/extra-addons /var/lib/odoo

# 7. Switch to Odoo user
USER odoo

# 8. Define Entrypoint
# Runs odoo-bin directly from the source folder
ENTRYPOINT ["python3", "/opt/odoo/odoo-bin"]

# Default command uses the config file
CMD ["-c", "/etc/odoo/odoo.conf"]