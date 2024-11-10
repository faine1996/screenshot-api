#!/bin/bash

echo "=== Process Status ==="
ps aux | grep -E 'python|chrome'

echo -e "\n=== Network Status ==="
netstat -tulpn

echo -e "\n=== Last 10 lines of API log ==="
tail -n 10 /var/log/api.log

echo -e "\n=== Memory Usage ==="
free -h

echo -e "\n=== Disk Usage ==="
df -h