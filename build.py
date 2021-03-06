import boto3
import argparse
import os
import socket
import time
import tests

parser = argparse.ArgumentParser(description='Build and cleanup script for Stelligent mini project')
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('--BUILD_ID', help="BUILD_ID")
parser.add_argument('--region', choices=["us-east-1", "us-east-2", "us-west-1"], help="AWS region", default="us-east-2", required=False)
parser.add_argument('--stack_name', help="A CloudFormation stack name unique to the AWS account and region this build is running against.", required=True)
group.add_argument('--decomm', action='store_true', help="Tear down everything built by this script. This argument cannot be used with the --s3_bucket_name argument.")
args = parser.parse_args()

build_id = str(args.BUILD_ID).lower()
region = str(args.region).lower()
stack_name = str(args.stack_name)
decomm = bool(args.decomm)
current_dir = os.path.dirname(os.path.realpath(__file__))
bad_states = [
	'CREATE_FAILED',
	'ROLLBACK_IN_PROGRESS',
	'ROLLBACK_FAILED',
	'ROLLBACK_COMPLETE',
	'DELETE_FAILED'
]
sock = socket.socket()


####### FUCNTIONS #######

def create_stack(template):
    cf = boto3.client('cloudformation', region_name = region)
    response = cf.create_stack(
        StackName=stack_name,
        TemplateURL='https://s3.us-east-2.amazonaws.com/theplacewiththefiles/' + template, 
        Parameters=[{'ParameterKey': 'buildv', 'ParameterValue': "v" + build_id}],
        Capabilities=['CAPABILITY_IAM'],
        Tags=[{'Key': 'build', 'Value': "v" + build_id}]
    )
    return response

def get_stack_id(stack):
    cf = boto3.client('cloudformation', region_name = region)
    response = cf.describe_stacks(StackName=stack)
    return response['Stacks'][0]['StackId']

def get_ip(stack):
    cf = boto3.client('cloudformation', region_name = region)
    response = cf.describe_stacks(StackName=stack)
    return response['Stacks'][0]['Outputs'][1]['OutputValue']

def get_instance_id(stack):
    cf = boto3.client('cloudformation', region_name = region)
    response = cf.describe_stacks(StackName=stack)
    return response['Stacks'][0]['Outputs'][0]['OutputValue']

def get_stack_status(stack):
    cf = boto3.client('cloudformation', region_name = region)
    response = cf.describe_stacks(StackName=stack)
    return response["Stacks"][0]["StackStatus"]

def delete_stack(stack):
    cf = boto3.client('cloudformation', region_name = region)
    response = cf.delete_stack(StackName=stack_id)
    return response

def get_instance_status(instance_id):
    ec2 = boto3.client('ec2', region_name = region)
    response = ec2.describe_instance_status(InstanceIds=[instance_id])
    return response["InstanceStatuses"][0]["InstanceStatus"]["Status"]

def get_system_status(instance_id):
    ec2 = boto3.client('ec2', region_name = region)
    response = ec2.describe_instance_status(InstanceIds=[instance_id])
    return response["InstanceStatuses"][0]["SystemStatus"]["Status"]

def delete_build():
    print('Deleting CloudFormation stack: ' + stack_name + '...')
    delete_stack(stack_id)
    print('Waiting for ' + stack_name + ' to be in DELETE_COMPLETE state...')
    while get_stack_status(stack_id) != 'DELETE_COMPLETE':
        stack_status = get_stack_status(stack_id)
        print('Current state of stack: ' + stack_status)
        if stack_status in bad_states:
            print('CloudFormation stack in ' + stack_status + ' state...' )
            print('You will need to investigate this CloudFormation stack and determine why it has not deleted.')
            print('Exiting build.')
            exit(1)
        time.sleep(30)
    print('Success! ' + stack_name + ' has reached state ' + stack_status + '!' )


####### BEGIN BUILD/DECOMM #######
if decomm:
    stack_id = get_stack_id(stack_name)
    delete_build()
    
    exit(0)
else:
    print('Creating CloudFormation stack: ' + stack_name + '...')
    try:
        create_stack('miniProject.json')
    except Exception as e:
        print(e)
        print('Try running this utility again once the decomm process is complete.')
        stack_id = get_stack_id(stack_name)
        delete_build()
        print('Exiting build.')
        exit(1)
    except:
        print('Unexpected error!')
        print('Try running this utility again once the decomm process is complete.')
        stack_id = get_stack_id(stack_name)
        delete_build()
        print('Exiting build.')
        exit(1)

    stack_id = get_stack_id(stack_name)

    print('Waiting for ' + stack_name + ' to be in CREATE_COMPLETE state...')
    while get_stack_status(stack_id) != 'CREATE_COMPLETE':
        stack_status = get_stack_status(stack_id)
        print('Current state of stack: ' + stack_status)
        if stack_status in bad_states:
            print('CloudFormation stack in ' + stack_status + ' state...' )
            print('Try running this utility again once the decomm process is complete.')
            delete_build()
            print('Exiting build.')
            exit(1)
        time.sleep(30)
    print('Success! ' + stack_name + ' has reached state ' + stack_status + '!' )

    instance_id = get_instance_id(stack_name)
    print('Checking status of app instance and waiting for "ok"')
    try:
        i = 0
        while (get_instance_status(instance_id) != 'ok') and (get_system_status(instance_id) != 'ok'):
            instance_status = get_instance_status(instance_id)
            system_status = get_system_status(instance_id)
            print('Instance status: ' + instance_status)
            print('System status: ' + system_status)
            i+=1
            if (instance_status == 'impaired') or (system_status == 'failed') or (i >= 10):
                print('There is something wrong with the app instance.')
                print('Try running this utility again once the decomm process is complete.')
                delete_build()
                print('Exiting build.')
                exit(1)
            time.sleep(30)
        print('Success! ' + instance_id + ' has become available!')
    except IndexError as e:
        print('Instance or system status was unreadable.')
        print('Try running this utility again once the decomm process is complete.')
        delete_build()
        print('Exiting build.')
        exit(1)
    except:
        print('Unexpected error!')
        print('Try running this utility again once the decomm process is complete.')
        delete_build()
        print('Exiting build.')
        exit(1)

    public_ip = get_ip(stack_name)
    connection = 'bad'
    x = 0
    while connection != 'good':
        try:
            print('Attempting to make connection to server over port 5000...')
            sock.connect((public_ip, 5000))
            connection = 'good'
        except:
            print('App server not ready to be connected to yet...')
            x+=1
            if x >= 20:
                print('The app server has taken too long to become available. Something is wrong...')
                print('Try running this utility again once the decomm process is complete.')
                delete_build()
                print('Exiting build.')
                exit(1)
            time.sleep(5)

    print('Build of miniProject complete! Connect to app: http://' + public_ip + ':5000/')

    exit(0)
