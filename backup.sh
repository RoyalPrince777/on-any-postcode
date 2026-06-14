#!/data/data/com.termux/files/usr/bin/bash

cd ~/oap

mkdir -p backups

cp app.py backups/app_$(date +%Y%m%d_%H%M%S).py

cp oap.db backups/oap_$(date +%Y%m%d_%H%M%S).db

echo "Backup Complete: $(date)"
