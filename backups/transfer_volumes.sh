#!/bin/bash
PROSERVER="root@tullahomabiblechurch.org"
DEVSERVER="root@tullahomabiblechurch.org"

VOLUMES="manna_joomla_html manna_mongodb_data manna_mysql_data manna_static_html"

while getopts "d:s:" arg; do
   case $arg in
      d )
        SERVER=${!OPTARG}
	for volume in $VOLUMES; do
	   echo "Dumping $volume from $SERVER"
	   ssh $SERVER docker run --rm -v $volume:/from alpine tar -C /from -czf - .> $volume.tar.gz
	done ;;
      s )
        SERVER=${!OPTARG}
	for volume in $VOLUMES; do
      	   echo "Pushing $volume to $SERVER"
	   cat $volume.tar.gz | ssh $SERVER 'docker run --rm -i -v ' $volume:/to 'alpine ash -c "cd /to ; tar -xzpvf - "'
        done ;;
   esac
done
