# simple bash script to launch a NextML instance/cluster with the key information provided
# note: this is senstiive to the REGION of the Keys; e.g. if the keys were created
# under the Ohio/us-east-2 region then you must launch into that region.
#
# I think the S3 bucket can be in any region
#
# This script should help take care of all of that

source ../../ApiKeys/aws_EC2_keys.sh
# NextML is still being ported to Python 3, needs Python 2 for
# its management scripts
source /hdd/nextml_env_py2/bin/activate # set up the python 2 virtual env

# run ec2 set up script, capture last line for the bucket name, export bucket name
# (source tmp) and remove the temporary file.
python next_ec2.py --region=$EC2_REGION --instance-type=$EC2_INSTANCE --key-pair=$KEY_PAIR --identity-file=$KEY_FILE createbucket $EC2_CLUSTER_NAME | tail -1 > tmp
source tmp
rm -f tmp
