FROM osrf/ros:humble-desktop

ENV DEBIAN_FRONTEND=noninteractive

# RF/system deps + SoapySDR Python bindings (not available via pip)
RUN apt-get update && apt-get install -y \
    gnuradio \
    rtl-sdr \
    hackrf \
    gqrx-sdr \
    aircrack-ng \
    tshark \
    python3-pip \
    python3-soapysdr \
    soapysdr-tools \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt requirements-ml.txt ./

RUN pip3 install --no-cache-dir -r requirements.txt --break-system-packages \
    && pip3 install --no-cache-dir -r requirements-ml.txt --break-system-packages

COPY . /app
ENV PYTHONPATH=/app

EXPOSE 5000

CMD ["python3", "scripts/ghoststack_ctl.py", "diagnose"]
