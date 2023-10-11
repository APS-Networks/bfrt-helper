from queue import Queue
from threading import Thread
from abc import ABC
from abc import abstractmethod

import grpc
import time
import os
from enum import Enum
from threading import Lock

from typing import List

from concurrent.futures import ThreadPoolExecutor
from threading import Lock, Event, Thread


import bfrt_helper.pb2.bfruntime_pb2_grpc as bfruntime_pb2_grpc
from bfrt_helper.pb2.bfruntime_pb2 import Update

from bfrt_helper.pb2.bfruntime_pb2 import (
    SetForwardingPipelineConfigRequest as SetPipelineReq,
)


from bfrt_helper.bfrt_info import BfRtInfo
from bfrt_helper.bfrt import make_empty_bfrt_helper
from bfrt_helper.bfrt import make_merged_config
from bfrt_helper.bfrt import make_port_map
from bfrt_helper.fields import PortId
from bfrt_helper.fields import DevPort
from bfrt_helper.match import Exact

from bfrt_helper.port import PortAN
from bfrt_helper.port import PortFEC
from bfrt_helper.port import PortSpeed




class BfRtStreamMonitorFuture:
    def __init__(self, timeout=5):
        self._isset = False
        self.value = None
        self.lock = Lock()
        self.expires = time.time() + timeout

    def result(self) -> any:
        while time.time() < self.expires:
            time.sleep(0.1)
            with self.lock:
                if self._isset:
                    return self.value
        raise Exception('Timeout')

    def set(self, value):
        with self.lock:
            self.value = value
            self._isset = True

    def __bool__(self) -> bool:
        try:
            self.result()
        except Exception as e:
            return False
        return True


class BfRtStreamMonitorState(Enum):
    OK = 0
    EXPIRED = 1
    COMPLETE = 2


class BfRtStreamMonitor:
    def __init__(self, function, future, timeout):
        self.function = function
        self.future = future
        self.expires = time.time() + timeout

    def execute(self, obj):
        if time.time() > self.expires:
            return BfRtStreamMonitorState.EXPIRED
        res = self.function(obj)
        if res is not None:
            self.future.set(res)
            return BfRtStreamMonitorState.COMPLETE
        return BfRtStreamMonitorState.OK


def received_subscribe(obj):
    return obj.HasField('subscribe')


def received_set_pipeline_response(obj):
    return obj.HasField('set_forwarding_pipeline_config_response')

GRPC_MAX_MSG_LEN_DEFAULT = 4194304
GRPC_MAX_MSG_LEN = GRPC_MAX_MSG_LEN_DEFAULT * 4

class BfRtClient:
    """ Barefoot Runtime gRPC Connection Class

    This class represents a an instance of the gRPC interface, which manages
    it's own connection.
    """
    def __init__(self, host, device_id, client_id):
        self.host = host
        self.channel = grpc.insecure_channel(self.host,
                options=[('grpc.max_send_message_length',    GRPC_MAX_MSG_LEN),
                         ('grpc.max_receive_message_length', GRPC_MAX_MSG_LEN)])
        self.client = bfruntime_pb2_grpc.BfRuntimeStub(self.channel)
        self.queue_out = Queue()
        self.queue_in = Queue()
        self.stream = self.client.StreamChannel(self.__stream_out())
        self.recv_thread = Thread(target=self.__stream_in)
        self.recv_thread.start()
        # self.on_message = None
        self.helper = make_empty_bfrt_helper(device_id, client_id)
        self.p4_name = None
        self.port_map = None
        self.program_name = None
        self.retrieve_config()

        self.executor = ThreadPoolExecutor(max_workers=4)
        self.monitors: List[BfRtClient.Monitor] = []
        self.monitor_lock = Lock()


    def expect(self, predicate, timeout=5) -> BfRtStreamMonitorFuture:
        ''' For convenience, If predicate is class name because it takes no
            arguments, instantiate it. '''
        if isinstance(predicate, type):
            predicate = predicate()
        with self.monitor_lock:
            future = BfRtStreamMonitorFuture(timeout)
            monitor = BfRtStreamMonitor(predicate, future, timeout)
            self.monitors.append(monitor)
            return future


    def retrieve_config(self):
        request = self.helper.create_get_pipeline_request()
        response = self.get_forwarding_pipeline(request)
        if len(response.config) > 0:
            self.p4_name = response.config[0].p4_name
        configs = make_merged_config(response)
        self.helper.bfrt_info = BfRtInfo(configs[0])

    def get_port_map(self, ports: list) -> dict:
        if self.p4_name is None:
            raise Exception('Cannot create port map without program name')
        self.port_map = make_port_map(self.p4_name, self.helper, self.client, ports)
        return self.port_map

    def __stream_out(self):
        """ """
        while True:
            p = self.queue_out.get()
            if p is None:
                break
            yield p

    def __stream_in(self):
        needs_monitor_remove = [
                BfRtStreamMonitorState.COMPLETE,
                BfRtStreamMonitorState.OK
            ]
        """ """
        try:
            for p in self.stream:
                with self.monitor_lock:
                    for monitor in self.monitors:
                        sts = monitor.execute(p)
                        if sts in needs_monitor_remove:
                            self.monitors.remove(monitor)
                if self.on_message is not None:
                    self.on_message(p)
                self.queue_in.put(p)
        except Exception as e:
            print(str(e))

    def write_table(
            self,
            table_name,
            key,
            program_name=None,
            action_name=None,
            action_params=None,
            update_type=Update.Type.INSERT):
        """ """
        if program_name is None and self.p4_name is None:
            raise Exception('Cannot write table without a program name')

        request = self.helper.create_table_write(
            program_name=program_name if program_name is not None else self.p4_name,
            table_name=table_name,
            key=key,
            action_name=action_name,
            action_params=action_params,
            update_type=update_type
        )
        return self.client.Write(request)


    def post(self, message):
        """ Post a message to BfRt """
        self.queue_out.put(message)

    def write(self, message):
        """ Write a message over BfRt """
        return self.client.Write(message)

    def get_forwarding_pipeline(self, request):
        """ """
        return self.client.GetForwardingPipelineConfig(request)

    def set_forwarding_pipeline(self, request):
        """ """
        self.client.SetForwardingPipelineConfig(request)

    def close(self):
        """ Close connection to the gRPC interface."""
        self.queue_out.put(None)
        self.recv_thread.join()

    @abstractmethod
    def on_message(self, msg):
        pass


    def __ensure_program_name(self):
        if self.program_name is None:
            raise Exception('Program name not set, you must bind to program')


    def __ensure_port_map(self):
        if self.port_map is None:
            raise Exception('Port list has not been set')


    def add_port(self, port: str, 
            speed: PortSpeed, 
            fec: PortFEC=PortFEC.NONE, 
            an: PortAN=PortAN.DEFAULT,
            enable=True):

        self.__ensure_program_name()
        self.__ensure_port_map()
        
        dev_port = self.port_map[port]
        request = self.helper.create_table_data_write(
            program_name=self.program_name,
            table_name='$PORT',
            key={
                '$DEV_PORT': Exact(DevPort(dev_port)) 
            },
            data={
                '$SPEED':            speed.value,
                '$FEC':              fec.value,
                '$AUTO_NEGOTIATION': an.value,
                '$PORT_ENABLE':      enable,
            })
        
        return self.write(request)


    def subscribe(self, learn=True, timeout=True, port_change=True):
        req = self.helper.create_subscribe_request(
            learn=True, 
            timeout=True,
            port_change=False)
        self.post(req)


    def bind(self, program_name):
        request = self.helper.create_set_pipeline_request(
                program_name,
                action=SetPipelineReq.BIND)

        self.set_forwarding_pipeline(request)
        self.program_name = program_name
        self.retrieve_config()


    def load_pipeline(self, program_name,
            bfrt_path,
            ctx_path,
            bin_path,
            bind=True):
        
        request = self.helper.create_set_pipeline_request(
                program_name,
                bfrt_path=bfrt_path,
                ctx_path=ctx_path,
                bin_path=bin_path)

        self.set_forwarding_pipeline(request)

        if bind: self.bind(program_name)


    def table_insert(self, table_name: str,
            key: dict,
            action_name: str=None,
            action_params: dict=None):
        request = self.helper.create_table_write( 
            program_name=self.program_name, 
            table_name=table_name,
            key=key,
            action_name=action_name,
            action_params=action_params)
        return self.client.Write(request)


    def create_multicast_node(self,
            id: int,
            rid: int,
            members: list,
            lags: list=[]):

        self.__ensure_program_name()
        self.__ensure_port_map()

        members_ = []
        for ii, member in enumerate(members):
            if isinstance(member, str):
                try:
                    members_.append(self.port_map[member])
                except KeyError as ke:
                    raise Exception(f'Port "{member}" not found')
            elif isinstance(member, int):
                members_.append(member)
            else:
                raise Exception(f'Member at index {ii} is neither string or int')


        request = self.helper.create_multicast_node_write(
                self.program_name,
                node_id=id,
                rid=rid,
                members=members_,
                lags=lags)
        
        return self.write(request)
    

    def create_multicast_group(self,
            id: int, 
            node_ids: list=[],
            xids: list=[],
            xid_valid: list=[]):
        assert len(node_ids) == len(xids) == len(xid_valid), 'Node, XID and XID valid lists must be same length'


        self.__ensure_program_name()
        
        request = self.helper.create_multicast_group_write(
                self.program_name,
                id, 
                nodes=node_ids,
                xids=xids,
                xid_valid_list=xid_valid)

        return self.write(request)
