#!/bin/bash
PROSERVER="ubuntu@tullahomabiblechurch.org"
DEVSERVER="ubuntu@dev.tullahomabiblechurch.org"

VOLUMES="manna_joomla_store manna_nginx_secrets manna_store"
for volume in $VOLUMES; do
   echo "Dumping $volume from $PROSERVER"
   ssh -i ~/lightsail.pem  $PROSERVER docker run --rm -v $volume:/from alpine tar -C /from -czf - .> $volume.pro.tar.gz
done

#TODO: Upload volumes to DEVSERVER
# ssh $DEVSERVER docker run --rm -i -v <TARGET_DATA_VOLUME_NAME>:/to alpine ash -c "cd /to ; tar -xpvf - " 
