from queue import Queue
from queue import Empty
from threading import Thread

import grpc

import bfrt_helper.pb2.bfruntime_pb2 as bfruntime_pb2
from bfrt_helper.pb2.bfruntime_pb2 import WriteRequest
from bfrt_helper.pb2.bfruntime_pb2 import Update

class BfRtConnection:
    """ Barefoot Runtime gRPC Connection Class

    This class represents a an instance of the gRPC interface, which manages
    it's own connection.
    """
    def __init__(self, host):#, helper):
        self.host = host
        self.channel = grpc.insecure_channel(self.host)
        self.client = bfruntime_pb2_grpc.BfRuntimeStub(self.channel)
        self.queue_out = Queue()
        self.queue_in = Queue()
        self.stream = self.client.StreamChannel(self.__stream_out())
        self.recv_thread = Thread(target=self.__stream_in)
        self.recv_thread.start()
        self.on_message = None


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