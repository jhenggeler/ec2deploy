README NOTES:  I made a decision to use public AMI's to speed up deployment.  I could have recreated a current publicly-listed amzn2 AMI on-the-fly with the ec2deploy script, but I felt that was a slower way to deploy.  It was also easier to create different AMI's with different root filesystems and make them public via AWS.  In an enterprise environment, the visibility of these AMI's would ideally be restricted to the AWS account for security.  Likewise, if there were other root filesystems that needed to be re-worked besides ext4, those AMI's would also need to be created and added to the AMI ID dictionary in the script, but frankly, it would be easier to add that into the configuration YAML to change that all through the configuration file.


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


   This program is ready to run as-is with a valid AWS account.  Example usage:   "ec2deploy.py -f awsconfig.yaml"

