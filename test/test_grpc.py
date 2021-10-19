import json
import os

from bfrt_helper.pb2.bfruntime_pb2 import Update

from bfrt_helper.bfrt import UnknownKeyField
from bfrt_helper.bfrt import UnknownTable
from bfrt_helper.bfrt import UnknownAction
from bfrt_helper.bfrt import UnknownActionParameter
from bfrt_helper.bfrt import MismatchedDataType
from bfrt_helper.bfrt import InvalidActionParameter
from bfrt_helper.bfrt import BfRtHelper
from bfrt_helper.bfrt_info import BfRtInfo
from bfrt_helper.fields import DevPort
from bfrt_helper.fields import Field
from bfrt_helper.fields import MACAddress
from bfrt_helper.fields import PortId
from bfrt_helper.match import Exact
from bfrt_helper.match import Ternary
from bfrt_helper.match import LPM


import pytest


DEVICE_ID = 0
CLIENT_ID = 0


class TooBigForAPortId(Field):
    bitwidth = 10

class NotUint32(Field):
    bitwidth = 33

class NotUint16(Field):
    bitwidth = 17


bfrt_file = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), 'resources/bfrt.json')

bfrt_data = json.loads(open(bfrt_file).read())
bfrt_info = BfRtInfo(bfrt_data)
bfrt_helper = BfRtHelper(DEVICE_ID, CLIENT_ID, bfrt_info)

def test_grpc_write_request_exact():
    write_request = bfrt_helper.create_table_write(
        program_name='test',
        table_name='pipe.TestIngressControl.port_forward_exact',
        key={
            'ig_intr_md.ingress_port': Exact(PortId(64))
        },
        action_name='TestIngressControl.forward',
        action_params={
            'egress_port': PortId(65),
        })

    update = write_request.updates[0]
    assert update.type == Update.INSERT

    table_entry = write_request.updates[0].entity.table_entry
    assert table_entry.table_id == 50148134
    assert table_entry.key.fields[0].field_id == 1
    assert table_entry.key.fields[0].exact.value == b'\x00\x40'
    assert table_entry.data.action_id == 29582296
    assert table_entry.data.fields[0].stream == b'\x00\x41'
    


def test_grpc_write_request_ternary():
    write_request = bfrt_helper.create_table_write(
        program_name='test',
        table_name='pipe.TestIngressControl.port_forward_ternary',
        key={
            'hdr.ethernet.srcAddr': Ternary(
                MACAddress('aa:bb:cc:dd:ee:ff'),
                MACAddress('ff:ff:ff:00:00:00'))
        },
        action_name='TestIngressControl.forward',
        action_params={
            'egress_port': PortId(65),
        })

    update = write_request.updates[0]
    assert update.type == Update.INSERT

    table_entry = write_request.updates[0].entity.table_entry
    assert table_entry.table_id == 38152076
    assert table_entry.key.fields[0].field_id == 1
    assert table_entry.key.fields[0].ternary.value == b'\xaa\xbb\xcc\x00\x00\x00'
    assert table_entry.key.fields[0].ternary.mask  == b'\xff\xff\xff\x00\x00\x00'
    assert table_entry.data.action_id == 29582296
    assert table_entry.data.fields[0].stream == b'\x00\x41'
    



def test_grpc_write_request_lpm():
    write_request = bfrt_helper.create_table_write(
        program_name='test',
        table_name='pipe.TestIngressControl.port_forward_lpm',
        key={
            'hdr.ethernet.srcAddr': LPM(
                MACAddress('aa:bb:cc:dd:ee:ff'), prefix=24)
        },
        action_name='TestIngressControl.forward',
        action_params={
            'egress_port': PortId(65),
        })

    update = write_request.updates[0]
    assert update.type == Update.INSERT

    table_entry = write_request.updates[0].entity.table_entry
    assert table_entry.table_id == 39533813
    assert table_entry.key.fields[0].field_id == 1
    assert table_entry.key.fields[0].lpm.value == b'\xaa\xbb\xcc\x00\x00\x00'
    assert table_entry.key.fields[0].lpm.prefix_len == 24
    assert table_entry.data.action_id == 29582296
    assert table_entry.data.fields[0].stream == b'\x00\x41'
    





def test_grpc_unknown_keyfield():
    with pytest.raises(UnknownKeyField):
        bfrt_helper.create_table_write(
            program_name='test',
            table_name='pipe.TestIngressControl.port_forward_exact',
            key={
                'non_existent_key': Exact(MACAddress('aa:bb:cc:dd:ee:ff'))
            },
            action_name='TestIngressControl.forward',
            action_params={
                'egress_port': PortId(65),
            })




def test_grpc_unknown_table():
    with pytest.raises(UnknownTable):
        write_request = bfrt_helper.create_table_write(
            program_name='test',
            table_name='pipe.TestIngressControl.non_existent_table',
            key={
                'ig_intr_md.ingress_port': Exact(PortId(64))
            },
            action_name='TestIngressControl.forward',
            action_params={
                'egress_port': PortId(65),
            })




def test_grpc_unknown_action():
    with pytest.raises(UnknownAction):
        write_request = bfrt_helper.create_table_write(
            program_name='test',
            table_name='pipe.TestIngressControl.port_forward_exact',
            key={
                'ig_intr_md.ingress_port': Exact(PortId(64))
            },
            action_name='TestIngressControl.non_existent_action',
            action_params={
                'egress_port': PortId(65),
            })




def test_grpc_unknown_action_parameter():
    with pytest.raises(UnknownActionParameter):
        write_request = bfrt_helper.create_table_write(
            program_name='test',
            table_name='pipe.TestIngressControl.port_forward_exact',
            key={
                'ig_intr_md.ingress_port': Exact(PortId(64))
            },
            action_name='TestIngressControl.forward',
            action_params={
                'non_existent_param': PortId(65),
            })




def test_grpc_unexpected_match_type_ternary():
    with pytest.raises(MismatchedDataType):
        bfrt_helper.create_table_write(
            program_name='test',
            table_name='pipe.TestIngressControl.port_forward_ternary',
            key={
                'hdr.ethernet.srcAddr': Exact(PortId(64))
            },
            action_name='TestIngressControl.forward',
            action_params={
                'egress_port': PortId(65),
            })




def test_grpc_unexpected_match_type_lpm():
    with pytest.raises(MismatchedDataType):
        bfrt_helper.create_table_write(
            program_name='test',
            table_name='pipe.TestIngressControl.port_forward_lpm',
            key={
                'hdr.ethernet.srcAddr': Exact(PortId(64))
            },
            action_name='TestIngressControl.forward',
            action_params={
                'egress_port': PortId(65),
            })




def test_grpc_unexpected_match_type_exact():
    with pytest.raises(MismatchedDataType):
        bfrt_helper.create_table_write(
            program_name='test',
            table_name='pipe.TestIngressControl.port_forward_exact',
            key={
                'ig_intr_md.ingress_port': Ternary(PortId(64))
            },
            action_name='TestIngressControl.forward',
            action_params={
                'egress_port': PortId(65),
            })




def test_grpc_invalid_action_parameter():
    with pytest.raises(InvalidActionParameter):
        bfrt_helper.create_table_write(
            program_name='test',
            table_name='pipe.TestIngressControl.port_forward_exact',
            key={
                'ig_intr_md.ingress_port': Exact(PortId(64))
            },
            action_name='TestIngressControl.forward',
            action_params={
                'egress_port': TooBigForAPortId(TooBigForAPortId.max_value()),
            })


