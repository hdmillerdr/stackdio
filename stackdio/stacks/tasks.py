import time
import os.path
from datetime import datetime

import envoy
import celery
from celery.utils.log import get_task_logger

from .models import Stack

logger = get_task_logger(__name__)


@celery.task(name='stacks.launch_stack')
def launch_stack(stack_id):
    try:
        stack = Stack.objects.get(id=stack_id)
        logger.info('Launching new stack: {0!r}'.format(stack))

        # Use SaltCloud to launch machines using the given stack's
        # map_file that should already be generated

        stack.status = 'launching'
        stack.save()

        # TODO: It would be nice if we could control the salt-cloud log
        # file at runtime

        # Get paths
        now = datetime.now().strftime('%Y%m%d_%H%M%S')
        map_file = stack.map_file.path
        log_file = stack.map_file.path + '.{}.log'.format(now)

        # Launch stack
        launch_cmd = ' '.join([
            'salt-cloud',
            '-y',                    # assume yes
            '-P',                    # parallelize VM launching
            '-lquiet',               # no logging on console
            '--log-file {0}',        # where to log
            '--log-file-level all',  # full logging
            '--out json',            # return JSON formatted results
            '--out-indent -1',       # don't format them; this is because of
                                     # a bug in salt-cloud
            '-m {1}',                # the map file to use for launching
        ]).format(log_file, map_file)

        logger.debug('Launch command: {0}'.format(launch_cmd))
        result = envoy.run(launch_cmd)

        if result.status_code > 0:
            stack.status = Stack.ERROR
            stack.status_detail = result.std_err \
                if len(result.std_err) else result.std_out
            stack.save()
            return

    except Stack.DoesNotExist:
        logger.error('Attempted to launch an unknown Stack with id {}'.format(stack_id))
    except Exception, e:
        logger.exception('Unhandled exception while launching a Stack')
        stack.status = 'error'
        stack.status_detail = str(e)
        stack.save()

@celery.task(name='stacks.provision_stack')
def provision_stack(stack_id):
    try:
        stack = Stack.objects.get(id=stack_id)
        logger.info('Provisioning stack: {0!r}'.format(stack))

        # Update status
        stack.status = 'provisioning'
        stack.save()

        # Run the appropriate top file
        provision_cmd = ' '.join([
            'salt',
            '-C',                   # compound targeting
            'G@stack_id:{}'.format(stack_id),  # target the nodes in this stack only
            'state.top',            # run this stack's top file
            stack.top_file.name,
            '--out yaml'            # output in yaml format
        ]).format(stack_id)

        logger.debug('Provision command: {0}'.format(provision_cmd))
        result = envoy.run(provision_cmd)

        logger.debug('salt state.top stdout:')
        logger.debug(result.std_out)

        logger.debug('salt state.top stderr:')
        logger.debug(result.std_err)

    except Stack.DoesNotExist:
        logger.error('Attempted to provision an unknown Stack with id {}'.format(stack_id))
    except Exception, e:
        logger.exception('Unhandled exception while provisioning a Stack')
        stack.status = 'error'
        stack.status_detail = str(e)
        stack.save()


@celery.task(name='stacks.finish_stack')
def finish_stack(stack_id):
    try:
        stack = Stack.objects.get(id=stack_id)
        logger.info('Finishing stack: {0!r}'.format(stack))

        # Update status
        stack.status = 'finished'
        stack.save()

    except Stack.DoesNotExist:
        logger.error('Attempted to provision an unknown Stack with id {}'.format(stack_id))
    except Exception, e:
        logger.exception('Unhandled exception while finishing a Stack')
        stack.status = 'error'
        stack.status_detail = str(e)
        stack.save()
