# Avi Networks CloudFormation AMI Lookup
This template is an example of how to dynamically lookup Avi Vantage AMIs when using CloudFormation templates.

## Pre-requsites
Your account must be able to create IAM roles and policies

## Usage
If using the CloudFormation UI, select which Avi Version you need the AMI value for. This example is intended to be used in Avi Controller deployments where instead of hard-coding each AMI version amongst the various regions, the AMI can be looked up during execution and provided to CloudFormation.