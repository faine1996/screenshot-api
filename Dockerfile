FROM debian:bullseye-slim

# Prevent interactive prompts during build
ENV DEBIAN_FRONTEND=noninteractive

# Install required packages
RUN apt-get update && apt-get install -y \
    qemu-system-x86 \
    qemu-utils \
    wget \
    cloud-utils \
    python3 \
    python3-pip \
    python3-venv \
    chromium \
    chromium-driver \
    sudo \
    openssh-client \
    curl \
    procps \
    net-tools \
    iproute2 \
    vim \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /vm

# Create necessary directories and user
RUN useradd -m -s /bin/bash vmuser && \
    mkdir -p /var/log/qemu && \
    mkdir -p /vm/screenshots && \
    mkdir -p /home/vmuser/screenshots && \
    mkdir -p /home/vmuser/logs && \
    mkdir -p /var/log && \
    touch /var/log/api.log && \
    chown -R vmuser:vmuser /home/vmuser && \
    chmod 755 /home/vmuser && \
    # Create Chrome directories and set permissions
    mkdir -p /tmp/.X11-unix && \
    chmod 1777 /tmp/.X11-unix && \
    mkdir -p /usr/share/fonts/truetype/chromium && \
    chmod -R 755 /usr/share/fonts/truetype/chromium

# Create virtual environment and install Python dependencies
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy API files
COPY api/ /vm/api/
RUN chmod +x /vm/api/monitor.sh

# Install Python dependencies
RUN pip install --no-cache-dir -r /vm/api/requirements.txt && \
    pip install selenium selenium-wire

# Make screenshot directory writable
RUN chmod 777 /vm/screenshots

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/ping || exit 1

# Runtime command
CMD ["python3", "-u", "/vm/api/screenshot_api.py"]