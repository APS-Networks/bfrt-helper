from bfrt_helper.bfrt_info import BfRtInfo
from bfrt_helper.bfrt import BfRtHelper
from bfrt_helper.fields import Exact
from bfrt_helper.fields import PortId
from bfrt_helper.fields import Field

import json

class DevPort(Field):
    bitwidth = 32


DEVICE_ID = 0
CLIENT_ID = 0

all_bfrt_data = json.load(open('all_bfrt.json'))

bfrt_info = BfRtInfo(all_bfrt_data)
helper = BfRtHelper(DEVICE_ID, CLIENT_ID, bfrt_info) 


request = helper.create_table_write(
    program_name='forwarder', 
    table_name='pipe.ForwarderIngressControl.port_forward',
    key={
        'ig_intr_md.ingress_port': Exact(PortId(55))
    },
    action_name='ForwarderIngressControl.forward',
    action_params={
        'egress_port': PortId(67),
    })

print(request)

request = helper.create_table_data_write(
    program_name='forwarder', 
    table_name='$PORT',
    key={
        '$DEV_PORT': Exact(DevPort(55))
    },
    data={
        '$SPEED': 'BF_SPEED_10G',
    })

print(request)

