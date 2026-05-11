FROM osrf/ros:humble-desktop

# Set environment
ENV DEBIAN_FRONTEND=noninteractive

# Install core RF and System dependencies
RUN apt-get update && apt-get install -y \
    gnuradio \
    rtl-sdr \
    hackrf \
    gqrx-sdr \
    aircrack-ng \
    tshark \
    python3-pip \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .

# Install Python requirements
RUN pip3 install --no-cache-dir -r requirements.txt --break-system-packages

# Copy GhostStack source
COPY . /app

# Expose Dashboard Port
EXPOSE 5000

# Default command
CMD ["python3", "scripts/ghoststack_ctl.py", "help"]
