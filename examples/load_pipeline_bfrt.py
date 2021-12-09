import signal
import struct
from queue import Queue
from queue import Empty
from threading import Thread

import grpc

import bfruntime_pb2
import bfruntime_pb2_grpc

HOST = '127.0.0.1:50052'
DEVICE_ID = 0


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


subscribe = bfruntime_pb2.Subscribe()
subscribe.device_id = 0

notifications = bfruntime_pb2.Subscribe.Notifications()
notifications.enable_learn_notifications = True
notifications.enable_idletimeout_notifications = True
notifications.enable_port_status_change_notifications = True

subscribe.notifications.CopyFrom(notifications)

request = bfruntime_pb2.StreamMessageRequest()
request.client_id = 1
request.subscribe.CopyFrom(subscribe)


stream_out_queue.put(request)
stream_in_queue.get()


request = bfruntime_pb2.SetForwardingPipelineConfigRequest()
request.action = bfruntime_pb2.SetForwardingPipelineConfigRequest.Action.VERIFY_AND_WARM_INIT_BEGIN_AND_END
request.dev_init_mode = bfruntime_pb2.SetForwardingPipelineConfigRequest.DevInitMode.FAST_RECONFIG

bfrt_data = open(BFRT_PATH, 'rb').read()
binary_data = open(BIN_PATH, 'rb').read()
context_data = open(CTX_PATH, 'rb').read()


config = bfruntime_pb2.ForwardingPipelineConfig()
config.p4_name = PROGRAM_NAME
config.bfruntime_info = bfrt_data

profile = bfruntime_pb2.ForwardingPipelineConfig.Profile()
profile.profile_name = 'pipe0'
profile.context = context_data
profile.binary = binary_data
profile.pipe_scope.extend([0, 1, 2, 3])

config.profiles.extend([profile])
request.config.extend([config])

client.SetForwardingPipelineConfig(request)
