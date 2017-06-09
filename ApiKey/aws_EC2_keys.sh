# These are very private AWS keys for spinning up EC2 services
# ... guard very carefully

# These keys are used to
# a) Launch NextML on EC2
# b) Make keys available for NextML managment via launch.py

export AWS_ACCESS_KEY_ID=[access-key]
export AWS_SECRET_ACCESS_KEY=[secret-key]
export KEY_FILE=/Users/scott/Classes/security/AWS/next_key_scott.pem  # the path to the key
export KEY_PAIR=next_key_scott  # the key I downloaded is next_key_scott.pem
export AWS_BUCKET_NAME=[buckid]
export NEXT_BACKEND_GLOBAL_HOST=[public-dns]
