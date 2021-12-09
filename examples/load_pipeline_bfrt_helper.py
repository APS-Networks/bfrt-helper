import signal
import struct
from queue import Queue
from queue import Empty
from threading import Thread

import grpc

import bfruntime_pb2
import bfruntime_pb2_grpc

from bfrt_helper.bfrt import BfRtHelper
from bfrt_helper.bfrt_info import BfRtInfo

HOST = '127.0.0.1:50052'
DEVICE_ID = 0
CLIENT_ID = 0


PROGRAM_NAME = 'port_forward'
CTX_PATH = '{}.tofino/pipe/context.json'.format(PROGRAM_NAME)
BIN_PATH = '{}.tofino/pipe/tofino.bin'.format(PROGRAM_NAME)
BFRT_PATH = '{}.tofino/bfrt.json'.format(PROGRAM_NAME)


channel = grpc.insecure_channel(HOST)
client = bfruntime_pb2_grpc.BfRuntimeStub(channel)

stream_out_queue = Queue() # Stream request channel (self._stream),
stream_in_queue = Queue() # Receiving messages from device


def stream_req_iterator():
    while True:
        p = stream_out_queue.get()
        if p is None:
            break
        print('Stream sending: ', p)
        yield p

def stream_recv(stream):
    try:
        for p in stream:
            print("Stream received: ", p)
            stream_in_queue.put(p)
    except Exception as e:
        print(str(e))


stream = client.StreamChannel(stream_req_iterator())
stream_recv_thread = Thread(target=stream_recv, args=(stream,))
stream_recv_thread.start()

def close(sig, frame):
    stream_out_queue.put(None)
    stream_recv_thread.join()

signal.signal(signal.SIGINT, close)


bfrt_data = json.loads(open("bfrt.json").read())
bfrt_info = BfRtInfo(bfrt_data)
bfrt_helper = BfRtHelper(DEVICE_ID, CLIENT_ID, bfrt_info)


request = bfrt_helper.create_subscribe_request()
stream_out_queue.put(request)
stream_in_queue.get()


request = bfrt_helper.create_set_pipeline_request(
    program_name=PROGRAM_NAME,
    bfrt_path=BFRT_PATH,
    context_path=CTX_PATH,
    binary_path=BIN_PATH)

client.SetForwardingPipelineConfig(request)


