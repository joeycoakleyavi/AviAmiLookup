#!/usr/bin/python
import boto3
import botocore.exceptions
import re
import cfnresponse

ec2 = boto3.client('ec2')

class AmiNotFound(Exception):
    pass
class OptInRequired(Exception):
    pass

def get_avi_version(ami):
    '''
    Pulls Avi Version out of an AMI Description
    '''
    regex = re.compile('\d+\.\d+\.\d+', re.IGNORECASE)
    m = regex.search(ami['Description'])
    return m.group() if m else None

def get_latest_ami_by_major_version(major_version, image_list):
    '''
    Get the latest version of a major release. I.E. if 20.x is specified and 20.1.1 - 20.1.6
    are available, choose 20.1.6

    Acceptable values as of 12/2021: Latest 18.x, Latest 20.x, Latest 21.x
    '''
    candidate_image = ""
    major_version_num = major_version.split(' ')[1].split('.')[0]

    for image in image_list:
        version = get_avi_version(image)
        if version and version.startswith(major_version_num):
            if not candidate_image:
                candidate_image = image
            elif version > get_avi_version(candidate_image):
                candidate_image = image
            else:
                pass

    if not candidate_image:
        raise AmiNotFound("No AMI could be found with the specified parameters")

    return candidate_image['ImageId']

def get_ami_by_version_number(version_number, image_list):
    for image in image_list:
        version = get_avi_version(image)
        if version and version_number in version:
            return image['ImageId']
    raise AmiNotFound("No AMI could be found with the specified parameters")

def test_ami_permissions(ami, event, context):
    try:
        response = ec2.run_instances(
            ImageId=ami,
            InstanceType='m5.2xlarge',
            DryRun=True,
            MaxCount=1,
            MinCount=1
        )
    except botocore.exceptions.ClientError as e:
        if e.response['Error'].get('Code') == 'DryRunOperation':
            pass
        elif e.response['Error'].get('Code') == 'OptInRequired':
            cfnresponse.send(event, context, cfnresponse.FAILED, {'Error': 'Product is not subscribed to in the AWS Marketplace.'})
        else:
            cfnresponse.send(event, context, cfnresponse.FAILED, {'Error': 'Unknown exception when testing AMI permissions'})

response = ec2.describe_images(
    Filters=[
        {
            "Name": "product-code",
            "Values": [
                "a9e7i60gidrc5x9nd7z3qyjj5"
            ]
        },
        {
            "Name": "state",
            "Values": [
                "available"
                ]
        }
    ]
)
images = response['Images']

def lambda_handler(event, context):
    requested_image = event['ResourceProperties']['ImageRequested']
    responseData = {}

    try:
        if event['RequestType'] == 'Delete':
            print('Delete Event Requested')
            return(cfnresponse.send(event, context, cfnresponse.SUCCESS, {}))

        if "Latest" in requested_image:
            ami = get_latest_ami_by_major_version(requested_image, images)
        else:
            ami = get_ami_by_version_number(requested_image, images)
        responseData['Ami'] = ami
        
    except Exception:
        responseData = {}
        responseData['Error'] = 'Execution error when performing AMI lookup. Please check logs'
        response = cfnresponse.send(event, context, cfnresponse.FAILED, responseData)
    
    test_ami_permissions(ami, event, context)
    
    cfnresponse.send(event, context, cfnresponse.SUCCESS, responseData)