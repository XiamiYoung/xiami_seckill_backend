#!/bin/bash -l

source $HOME/.bash_profile
systemctl start redis
cd /root/xiami_seckill/node-server/
sh startServer.sh
cd /root/xiami_seckill/xiami_seckill_backend/
sh startServer.sh