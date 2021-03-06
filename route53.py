import boto3
import argparse
import time


parser = argparse.ArgumentParser(description='Input the IP I need')
parser.add_argument('--BUILD_ID', required=True)
args = parser.parse_args()


build_id = str(args.BUILD_ID).lower()


cf = boto3.client('cloudformation')


response = cf.describe_stacks(StackName='demoStack' + build_id)
new_ip = response['Stacks'][0]['Outputs'][1]['OutputValue']


r53 = boto3.client('route53')
r53.change_resource_record_sets(
    HostedZoneId='Z3JLKIWI026135',
    ChangeBatch={
        'Comment': 'Updating to new version',
        'Changes': [
            {
                'Action': 'UPSERT',
                'ResourceRecordSet': {
                    'Name': 'app.peter-g.net',
                    'Type': 'A',
                    'TTL': 0,
                    'ResourceRecords': [
                        {
                            'Value': new_ip
                        }
                    ]
                }
            },
        ]
    }
)


# time.sleep(15)


# stack_list = cf.list_stacks(StackStatusFilter=['CREATE_COMPLETE'])
# stack_sums = stack_list['StackSummaries']
# for cfstack in stack_sums:
#     stack_name = cfstack['StackName']
#     if stack_name != 'demoStack' + build_id:
#         cf.delete_stack(StackName=stack_name)
