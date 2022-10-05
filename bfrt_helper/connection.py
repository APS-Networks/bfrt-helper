from queue import Queue
from queue import Empty
from threading import Thread

import grpc

import bfrt_helper.pb2.bfruntime_pb2 as bfruntime_pb2
import bfrt_helper.pb2.bfruntime_pb2_grpc as bfruntime_pb2_grpc
from bfrt_helper.pb2.bfruntime_pb2 import WriteRequest
from bfrt_helper.pb2.bfruntime_pb2 import Update

from bfrt_helper.bfrt import make_empty_bfrt_helper
from bfrt_helper.bfrt import make_merged_config
from bfrt_helper.bfrt import make_port_map
from bfrt_helper.fields import PortId


class PortMap:
    def __init__(self, data):
        self.data = data

    def __getitem__(self, key):
        return PortId(self.data[key])

class BfRtConnection:
    """ Barefoot Runtime gRPC Connection Class

    This class represents a an instance of the gRPC interface, which manages
    it's own connection.
    """
    def __init__(self, host, device_id, client_id):#, helper):
        self.host = host
        self.channel = grpc.insecure_channel(self.host)
        self.client = bfruntime_pb2_grpc.BfRuntimeStub(self.channel)
        self.queue_out = Queue()
        self.queue_in = Queue()
        self.stream = self.client.StreamChannel(self.__stream_out())
        self.recv_thread = Thread(target=self.__stream_in)
        self.recv_thread.start()
        self.on_message = None
        self.helper = make_empty_bfrt_helper(device_id, client_id)
        self.p4_name = None
        self.retrieve_config()

    def retrieve_config(self):
        request = self.helper.create_get_pipeline_request()
        response = self.get_forwarding_pipeline(request)
        if len(response.config) > 0:
            self.p4_name = response.config[0].p4_name
        configs = make_merged_config(response)
        self.helper.bfrt_info = BfRtInfo(configs[0])

    def get_port_map(self, ports: list) -> PortMap:
        if self.p4_name is None:
            raise Exception('Cannot create port map without program name')
        port_map = make_port_map(self.p4_name, self.helper, self.client, ports)
        return PortMap(port_map)

    def __stream_out(self):
        """ """
        while True:
            p = self.queue_out.get()
            if p is None:
                break
            yield p

    def __stream_in(self):
        """ """
        try:
            for p in self.stream:
                if self.on_message != None:
                    self.on_message(p)
                else:   
                    self.queue_in.put(p)
        except Exception as e:
            print(str(e))

    def write_table(self,
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