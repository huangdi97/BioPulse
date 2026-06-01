#!/bin/bash
set -e
apt install -y python3 python3-pip
pip3 install fastapi uvicorn python-jose passlib python-multipart bcrypt
echo "DONE"
