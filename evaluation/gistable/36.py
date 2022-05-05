import time
import logging

import boto3
import luigi

POLL_TIME = 2
client = boto3.client('ecs')
logger = logging.getLogger('luigi-interface')


def _get_task_status(task_ids):
    '''Retrieve task status from ECS API

    Returns one of {RUNNING|PENDING|STOPPED}
    '''
    response = client.describe_tasks(tasks=task_ids)

    # Error checking
    if response['failures'] != []:
        raise Exception('There were some failures:\n{0}'.format(response['failures']))
    status_code = response['ResponseMetadata']['HTTPStatusCode']
    if status_code != 200:
        raise Exception('Task status request received status code {0}:\n{1}'.format(
            status_code, response))

    return [t['lastStatus'] for t in response['tasks']]


def _track_task(task_ids):
    '''Poll task status until STOPPED'''
    while True:
        statuses = _get_task_status(task_ids)
        if all([status == 'STOPPED' for status in statuses]):
            logger.info('ECS tasks {0} STOPPED'.format(','.join(task_ids)))
            break
        time.sleep(POLL_TIME)
        logger.debug('ECS task status for tasks {0}: {1}'.format(
            ','.join(task_ids), status))


class ECSTask(luigi.Task):

    '''Base class for an EC2 Container Service Task

    task_def_arn: task definition ARN, of the form 
        'arn:aws:ecs:<region>:<user_id>:task-definition/<family>:<tag>'
    overrides: list of dicts with keys 'name' and 'command', describing the
        container names and commands to override in the task definition. Example:
            [{name': 'myContainer', 'command': ['/bin/sleep', '60']}]
    '''

    task_def_arn = luigi.Parameter()
    overrides = luigi.Parameter(is_list=True)

    def run(self):
        # Submit the task to AWS ECS and get assigned task ID
        response = client.run_task(taskDefinition=self.task_def_arn,
            overrides={"containerOverrides": self.overrides})
        task_ids = [task['taskArn'] for task in response['tasks']]

        # Wait on task completion
        _track_task(task_ids)
