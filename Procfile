web: gunicorn -b 0.0.0.0:8001 -w ${WORKERS:-4} -t 120 -e SCRIPT_NAME=/manna 'manna:app'
