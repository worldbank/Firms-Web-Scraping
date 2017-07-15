export HIT_MAX_AWARD=0.50 # maximum spend per hit, in USD, per verified business in region
export INPUT_FILE=$PWD/../../../../example_input.csv
export FLASK_APP=flaskr
#export FLASK_DEBUG=true
export HOST=0.0.0.0 #127.0.0.1 if you want local only
export PORT=5000
gunicorn -w 8 -b $HOST:$PORT flaskr:app --timeout 120 --log-level debug --access-logfile -
# the below is too slow in a "production" env, even against MTurk which is pretty slow
#python3 -m flask run --host=$HOST --port=$PORT
