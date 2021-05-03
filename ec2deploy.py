#!/bin/python3
"""
   Program:  ec2deploy.py
   Usage:    ec2deploy.py -h  --  Help
             ec2deploy.py -f [config file]
                 where [config file] is custom
   Author:   Joe Henggeler
   Assumptions: This program assumes:
       1. The user account executing this program has already been set up previously with "aws configure" (and the secret keys are already stored)
       2. Using python3 and the python3 executable is in /bin/python3
       3. Dependencies below are already installed and working on the user's machine (pip, json, boto3, yaml)
       4. Admin AWS permissions are set for the user executing this script for ec2 instances, keypairs, and security groups.
       5. Because of the ext4 ("/") special case requirement, limitations have been set up for this to be run in us-east-1 from a specific AMI I created and made public to make this easier.
       6. Does not cover all filesystems types for / (the root filesystem), but can be added in later revisions. 
       7. The assumption for the 4th requirement for / (the root filesystem) was that the users could write where they had permissions to write ( not to all of / ).
       8. This isn't quite production-ready with defined functions and main.  But it is simple to add that in after the fact.
"""

import argparse
import json
import boto3
from botocore.config import Config
from params import Parameters

"""  Parameter definitions.  Could have easily been put into the configuration yaml """
defaultsecgrp = 'secgrp2'
keyuser = 'key_user2'

"""  Set the configuration for AWS to us-east-1 to enable use of the public AMI's in that region   """
awsconfig = Config(region_name = 'us-east-1', signature_version = 'v4', retries = { 'max_attempts': 10, 'mode': 'standard' })

"""  Simple ArgParse  """
parse = argparse.ArgumentParser(description="AWS Command Line w/configuration file")
parse.add_argument("-f","--config_file", help="AWS Configuration file")
arg1 = parse.parse_args()
config = Parameters('awsconfig.yaml')
    
"""  Formulation of part I of the user_data scripts based upon the users in the configuration file """
user_data = '#!/bin/bash\n'
for u in config.server.users:
    user_data = user_data + 'useradd ' + u['login'] + '\nmkdir -p /home/' + u['login'] + '/.ssh\nchown ' + u['login'] + ':' + u['login'] + ' /home/'+ u['login'] + '/.ssh\necho "' + u['ssh_key'] + '" >> /home/' + u['login'] + '/.ssh/authorized_keys\nchmod 700 /home/' + u['login'] + '/.ssh\nchown ' + u['login'] + ':' + u['login'] + ' /home/' + u['login'] + '/.ssh/authorized_keys\nchmod 600 /home/' + u['login'] + '/.ssh/authorized_keys\n'


"""  AMI Index Dictionary.  To be added to later for more root volume options.  Speeds up the deployment """
amiindex = {
            'ext4': 'ami-04108d64a147ddb9a',
            'xfs': 'ami-048f6ed62451373d9'
           }
"""  Setting the AMI and formulating the volumes needed for launch                         """
"""  and formulation of part II of the user_data scripts based upon the volumes configured """
for v in config.server.volumes:
    if (v['mount'] == '/'):
        amiid=amiindex.get(v['type'])
    else:
        user_data1 = 'printf "n\np\n\n\n\nt\n83\nw\n" | fdisk ' + v['device'] + '\nmkfs.' + v['type'] + ' ' + v['device'] + '1\necho "' + v['device'] + '1  ' + v['mount'] + '  ' + v['type'] + '   defaults    0   0" >> /etc/fstab\nmkdir -p ' + v['mount'] + '\nchmod 777 ' + v['mount'] + '\nmount ' + v['mount'] + '\nchmod 777 ' + v['mount'] + '\n'
    blockdevmappings = [
                         {
                            'DeviceName': v['device'],
                            'Ebs': {
                                 'DeleteOnTermination': False,
                                 'VolumeSize': v['size_gb'],
                                 'VolumeType': 'gp2',
                                 'Encrypted': False
                               },
                         },
                       ] 

  
"""  Starting the boto3 instance """
client = boto3.client('ec2', config=awsconfig)

"""  Simple filters to attempt to pull the correct AMI we wish to use.  This needs to be modified based on more questions. """
try:
    response = client.describe_images(
        Filters=[
            {
                'Name': 'name',
                'Values': ['amzn2*']
            },
            {
                'Name': 'architecture',
                'Values': [config.server.architecture]
            },
            {
                'Name': 'virtualization-type',
                'Values': [config.server.virtualization_type]
            },
            {
                'Name': 'root-device-type',
                'Values': [config.server.root_device_type]
            },
            {
                'Name': 'image-id',
                'Values': [amiid]
            },
        ]
    )
except:
    print(f"ERROR: Issue querying for AMI images")
imageId = response['Images'][0]['ImageId']


""" Establishing the EC2 resource """
ec2 = boto3.resource('ec2',config=awsconfig)


""" Creating a keypair.  Not really needed, but helpful in troubleshooting.  Ignored if it fails if in case it has already been run once """
try:
    userkey = ec2.create_key_pair(
        KeyName=keyuser,
    )
except:
    print(f"WARNING: Issue creating a new keypair.  This could be because it already exists.")


""" Creating a new security group we need since we don't have a specified one to use.  Ignored if it fails if it has already been run once """
try:
     sec = ec2.create_security_group(GroupName='secgrp2', Description='Allow SSH')
except:
    print(f"WARNING: Issue creating a new security group.  This could be because it already exists.")


""" Setting the rules for SSH from external sources """
try:
     sec.authorize_ingress(CidrIp='0.0.0.0/0', IpProtocol='tcp', FromPort=22, ToPort=22)
except:
     print(f"WARNING: Issue adding a rule into the created security group.  This could be because it is already set up.")


""" Creating the actual ec2 instance """
try:
     instance1 = ec2.create_instances(
            BlockDeviceMappings=blockdevmappings,
            SecurityGroupIds=[
                defaultsecgrp,
            ],
            ImageId=imageId,
            MinCount=config.server.min_count,
            MaxCount=config.server.max_count,
            InstanceType=config.server.instance_type,
            UserData=user_data+user_data1,
            KeyName='key_user2',
     )
except:
     print(f"ERROR:  There was an error creating the image.")

instance=instance1[0]


""" Anything past this point can be deleted for faster deploys if necessary.  These are added in to aid in speeding up verification of the requirements. """


""" Creating a waiter to wait on the instance running status """
waiter = ec2.meta.client.get_waiter('instance_running')
waiter.wait(InstanceIds=[instance.id])

""" Creating a waiter to wait on the Instance status OK """
waiter = ec2.meta.client.get_waiter('instance_status_ok')
waiter.wait(InstanceIds=[instance.id])

""" Reloading the instance details """
instance.load()

""" Printing the information for the user to attempt to try """
print('The created instance ID is: ' + instance.id)
print('The public DNS name of the instance is: ' + instance.public_dns_name)
