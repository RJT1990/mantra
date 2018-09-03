from mantraml.ui.core.models import Cloud
from mantraml.ui.core.consts import MANTRA_DEVELOPMENT_TAG_NAME

import datetime
import pytest


class InstanceFilter1:

    tags = [{'Value': MANTRA_DEVELOPMENT_TAG_NAME}]
    instance_type = 'p2.large'
    id = 'i-eafeafeea'
    state = {'Name': 'running'}
    launch_time = datetime.datetime.now()

class InstanceFilter2:

    tags = [{'Value': 'Other Tag'}]
    instance_type = 'p5.large'
    id = 'i-feeafeea'
    state = {'Name': 'stopped'}
    launch_time = datetime.datetime.now()

def test_get_instance_metadata():

    # dev
    instance_obj = InstanceFilter1()
    instance_data_1 = Cloud.get_instance_metadata([instance_obj], no_dev=False)
    assert(instance_data_1[0]['name'] == instance_obj.tags[0]['Value'])
    assert(instance_data_1[0]['type'] == instance_obj.instance_type)
    assert(instance_data_1[0]['id'] == instance_obj.id)
    assert(instance_data_1[0]['tags'] == ['development'])
    assert(instance_data_1[0]['state'] == 'running')
    assert(instance_data_1[0]['launch_time'] == instance_obj.launch_time)

    instance_data_1b = Cloud.get_instance_metadata([instance_obj], no_dev=True)
    assert(instance_data_1b == [])

    instance_obj_2 = InstanceFilter2()

    instance_data_2 = Cloud.get_instance_metadata([instance_obj_2])
    assert(instance_data_2[0]['name'] == instance_obj_2.tags[0]['Value'])
    assert(instance_data_2[0]['type'] == instance_obj_2.instance_type)
    assert(instance_data_2[0]['id'] == instance_obj_2.id)
    assert(instance_data_2[0]['tags'] == [])
    assert(instance_data_2[0]['state'] == 'stopped')
    assert(instance_data_2[0]['launch_time'] == instance_obj_2.launch_time)
