#!/bin/bash
PROSERVER="ubuntu@tullahomabiblechurch.org"
DEVSERVER="ubuntu@dev.tullahomabiblechurch.org"

VOLUMES="manna_joomla_html manna_mongodb_data manna_mysql_data manna_nginx_secrets"
for volume in $VOLUMES; do
   echo "Dumping $volume from $PROSERVER"
   ssh -i ~/Desktop/lightsail.pem  $PROSERVER \
      set -x
      docker run --rm -v $volume:/from \
         alpine ash -c "cd /from ; tar -czf - . " \
            > $volume.pro.tar.gz
      set +x
done

#TODO: Upload volumes to DEVSERVER
# ssh $DEVSERVER docker run --rm -i -v <TARGET_DATA_VOLUME_NAME>:/to alpine ash -c "cd /to ; tar -xpvf - " 