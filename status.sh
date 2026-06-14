#!/data/data/com.termux/files/usr/bin/bash

echo "====================="
echo "OAP STATUS REPORT"
echo "====================="

echo
echo "FILES:"
ls -lh app.py oap.db 2>/dev/null

echo
echo "BACKUPS:"
ls backups 2>/dev/null | tail -10

echo
echo "DATABASE SIZE:"
du -h oap.db 2>/dev/null

echo
echo "FLASK PROCESS:"
ps -ef | grep python | grep app.py

echo
echo "PORT CHECK:"
ss -tulpn | grep 5000

echo
echo "DATE:"
date

echo
echo "STATUS COMPLETE"
