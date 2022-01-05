import bfrt_helper.pb2.bfruntime_pb2 as bfruntime_pb2

from bfrt_helper.pb2.bfruntime_pb2 import (
    SetForwardingPipelineConfigRequest as SetPipelineReq
)

from bfrt_helper.match import Exact
from bfrt_helper.match import LongestPrefixMatch
from bfrt_helper.match import Ternary
from bfrt_helper.fields import Field


class UnknownAction(Exception):
    """Exception raised when an action for a given table could not be found.

    Args:
        table_name (str): String containing the name of the table.
        action_name (str): String containing the name of the action.
    """

    def __init__(self, table_name, action_name):
        msg = f"Could not find action {table_name}::{action_name}"
        super().__init__(msg)


class UnknownActionParameter(Exception):
    """Exception raised when a action parameter for a given table could not be
    found.

    Some tables have associated parameters with them; these are optional.
    These are applied to an action, for example (in P4)::

        action send_to_multicast_group(MulticastGroupId_t group) {
            ingress_metadata.multicast_grp_a = group;
        }


    Args:
        table_name (str): String containing the name of the table.
        action_name (str): String containing the name of the action.
        param_name (str): String containing the name of the parameter.
    """

    def __init__(self, table_name, action_name, param_name):
        msg = (
            'Could not find action parameter ',
            f'{table_name}::{action_name}::{param_name}'
        )
        super().__init__(msg)


class UnknownTable(Exception):
    """Exception raised when a given table could not be found.

    Args:
        table_name (str): String containing the name of the table.
    """

    def __init__(self, table_name):
        super().__init__(f"Could not find table {table_name}")


class UnknownKeyField(Exception):
    """Exception raised when a key field for a given table could not be found.

    A key field is a part of the match construct, and includes a name and
    data. When a table is executed, the key field names are used to retrieve
    a value with the same name as defined in either metadata or headers. This
    value is compared with the key field's data on the basis of the fields
    defined match type::

        table multicast {
            key = {
                hdr.vlan.id: exact;
            }
            actions = {
                send_to_multicast_group;
            }
            const entries = {
                100: send_to_multicast_group;
            }
        }

    In this example, a key is defined to match on a vlan id which has been
    parsed into the program's headers. The key field's name in this case is
    ``hdr.vlan.id`` and it's match type is ``exact``. If the name of this field
    is not defined, in some operations this exception will be raised.

    Args:
        table_name (str): String containing the name of the table.
        action_name (str): String containing the name of the action.
    """

    def __init__(self, table_name, field_name):
        super().__init__(f"Could not find key field {table_name}::{field_name}")


class MismatchedMatchType(Exception):
    """Exception raised when the match for a key field declared in a request
    does not match that which is defined in the table.

    The current accepted match types are:

        * :ref:`LongestPrefixMatch`
        * :ref:`Exact`
        * :ref:`Ternary`

    Args:
        field_name (str): The name of the field in question.
        field_data (Field): The instance of the incorrect field.
        expected (str): The name of the expected data type.
    """

    def __init__(self, field_name, field_data, expected: str):
        clz = field_data.__class__.__name__
        msg = (f'Expected field type for {field_name} is {expected}, but have ',
               f'{clz}')
        super().__init__(msg)


class MismatchedDataSize(Exception):
    """Exception raised when the data size of a field in a request does not
    match that which is registered to the table.

    Most fields have an associated bitwidth. This is defined in the P4 program,
    and is presented in the BfRt info file if generated. While we can't do
    strict type checking, we can compare the bitwidths of the input and target
    fields (any field registered in this library, or defined by the user, will
    be equivalent to any other field with the same bitwidth).

    Args:
        expected (int): Bitwidth of field as defined by P4 program.
        observed (int): Bitwidth of field presented by the user.
    """

    def __init__(self, expected, observed):
        msg = f"Expected data size {expected} but have {observed}"
        super().__init__(msg)


class InvalidActionParameter(Exception):
    def __init__(self, table_name, action_name, param_name, reason):
        msg = f"{table_name}::{action_name}::{param_name}: {reason}"
        super().__init__(msg)


class BfRtHelper:
    def __init__(self, device_id, client_id, bfrt_info):
        self.device_id = device_id
        self.client_id = client_id
        self.bfrt_info = bfrt_info

    def create_subscribe_request(
        self,
        learn=True,  # Receive learn notifications
        timeout=True,  # Receive timeout notifications
        port_change=True,  # Receive port state change notifications
        request_timeout=10,  # Subscribe response timeout
    ):
        """Create a subscribe request for registering with a device.

        After a gRPC connection has been established between a client and the
        Barefoot Runtime server, a ``subscribe`` request must be issued by the
        client in order for the runtime to act on commands issued by the client
        as well as send and receive any other messages.

        Args:
            learn (bool, optional): Enable learn notifications. Provided through
                digest messages from the gRPC stream channel. Default is
                ``True``.

            timeout (bool, optional): Receive timeout notifications. Default is
                ``True``.

            port_change (bool, optional): Receive port state change
                notifications. Default is ``True``.

            request_timeout (int, optional): Default is ``10``.

        """

        subscribe = bfruntime_pb2.Subscribe()
        subscribe.device_id = self.device_id

        notifications = bfruntime_pb2.Subscribe.Notifications()
        notifications.enable_learn_notifications = learn
        notifications.enable_idletimeout_notifications = timeout
        notifications.enable_port_status_change_notifications = port_change

        subscribe.notifications.CopyFrom(notifications)

        request = bfruntime_pb2.StreamMessageRequest()
        request.client_id = self.client_id
        request.subscribe.CopyFrom(subscribe)

        return request

    def create_write_request(
        self,
        program_name,
        atomicity=bfruntime_pb2.WriteRequest.Atomicity.CONTINUE_ON_ERROR,
    ):
        request = bfruntime_pb2.WriteRequest()
        request.client_id = self.client_id
        request.p4_name = program_name
        request.atomicity = atomicity

        target = bfruntime_pb2.TargetDevice()
        target.device_id = self.device_id
        target.pipe_id = 0xFFFF
        target.direction = 0xFF
        target.prsr_id = 0xFF

        request.target.CopyFrom(target)

        return request

    def create_read_request(self, program_name):
        request = bfruntime_pb2.ReadRequest()
        request.client_id = self.client_id
        request.p4_name = program_name
        # request.atomicity = atomicity

        target = bfruntime_pb2.TargetDevice()
        target.device_id = self.device_id
        target.pipe_id = 0xFFFF
        target.direction = 0xFF
        target.prsr_id = 0xFF

        request.target.CopyFrom(target)

        return request

    def create_table_entry(self, table_name):
        table_id = self.bfrt_info.get_table_id(table_name)
        if table_id is None:
            raise UnknownTable(table_name)
        table_entry = bfruntime_pb2.TableEntry()
        table_entry.table_id = table_id

        return table_entry

    def create_key_field(self, table_name, field_name, data):
        info_key_field = self.bfrt_info.get_key(table_name, field_name)
        if info_key_field is None:
            raise UnknownKeyField(table_name, field_name)
        bfrt_key_field = bfruntime_pb2.KeyField()
        bfrt_key_field.field_id = info_key_field.id

        if info_key_field.match_type == "Exact":
            if not isinstance(data, Exact):
                raise MismatchedMatchType(field_name, data, "Exact")
            bfrt_key_field.exact.value = data.value_bytes()

        if info_key_field.match_type == "LongestPrefixMatch":
            if not isinstance(data, LongestPrefixMatch):
                raise MismatchedMatchType(field_name, data, "LongestPrefixMatch")
            bfrt_key_field.lpm.value = data.value_bytes()
            bfrt_key_field.lpm.prefix_len = data.prefix

        if info_key_field.match_type == "Ternary":
            if not isinstance(data, Ternary):
                raise MismatchedMatchType(field_name, data, "Ternary")
            bfrt_key_field.ternary.value = data.value_bytes()
            bfrt_key_field.ternary.mask = data.mask_bytes()

        return bfrt_key_field

    def create_data_field(self, field, value):
        data_field = bfruntime_pb2.DataField()
        data_field.field_id = field.id

        if isinstance(value, Field) or isinstance(value, bytes):
            if field.type["type"] == "bytes":
                if value.bitwidth != field.type["width"]:
                    raise MismatchedDataSize(field.type["width"],
                                             value.bitwidth)
            elif field.type["type"] == "uint16":
                if value.bitwidth != 16:
                    raise MismatchedDataSize(field.type["width"],
                                             value.bitwidth)
            elif field.type["type"] == "uint32":
                if value.bitwidth != 32:
                    raise MismatchedDataSize(field.type["width"],
                                             value.bitwidth)
            data_field.stream = value.to_bytes()
        elif isinstance(value, float):
            data_field.float_val = value
        elif isinstance(value, str):
            data_field.str_val = value
        elif isinstance(value, bool):
            data_field.bool_val = value
        elif isinstance(value, list):
            if len(value) > 0:
                inner_value = value[0]
                if isinstance(inner_value, int):
                    data_field.int_arr_val.val.extend(value)
                elif isinstance(inner_value, bool):
                    data_field.bool_arr_value.val.extend(value)
                else:
                    data = [self.create_data_field(x) for x in value]
                    data_field.container_arr_value.val.extend(data)
        else:
            raise Exception("Unknown data type!")
        return data_field

    def create_key_fields(self, table_name, key_fields):
        fields = []
        for field_name, field_data in key_fields.items():
            field = self.create_key_field(table_name, field_name, field_data)
            fields.append(field)

        return fields

    def create_action(self, table_name, action_name, action_params):
        info_action = self.bfrt_info.get_action_spec(table_name, action_name)
        if info_action is None:
            raise UnknownAction(table_name, action_name)

        bfrt_table_data = bfruntime_pb2.TableData()
        bfrt_table_data.action_id = info_action.id

        if action_params is not None:
            for param_name, param_data in action_params.items():
                info_action_field = self.bfrt_info.get_action_field(
                    table_name, action_name, param_name
                )

                if info_action_field is None:
                    raise UnknownActionParameter(table_name, action_name,
                                                 param_name)

                try:
                    bfrt_data_field = self.create_data_field(
                        info_action_field, param_data
                    )
                    bfrt_table_data.fields.extend([bfrt_data_field])
                except MismatchedDataSize as err:
                    raise InvalidActionParameter(
                        table_name, action_name, param_name, str(err)
                    )

        return bfrt_table_data

    def create_table_write(
        self,
        program_name,
        table_name,
        key,
        action_name=None,
        action_params=None,
        update_type=bfruntime_pb2.Update.Type.INSERT,
    ):
        bfrt_request = self.create_write_request(program_name)
        bfrt_table_entry = self.create_table_entry(table_name)
        bfrt_key_fields = self.create_key_fields(table_name, key)
        bfrt_table_entry.key.fields.extend(bfrt_key_fields)

        if action_name is not None:
            bfrt_action = self.create_action(table_name, action_name,
                                             action_params)
            bfrt_table_entry.data.CopyFrom(bfrt_action)

        bfrt_update = bfrt_request.updates.add()
        bfrt_update.type = update_type
        bfrt_update.entity.table_entry.CopyFrom(bfrt_table_entry)

        return bfrt_request

    def create_table_data_write(
        self,
        program_name,
        table_name,
        key,
        data,
        update_type=bfruntime_pb2.Update.Type.INSERT,
    ):
        bfrt_request = self.create_write_request(program_name)
        bfrt_table_entry = self.create_table_entry(table_name)
        bfrt_key_fields = self.create_key_fields(table_name, key)
        bfrt_table_entry.key.fields.extend(bfrt_key_fields)

        bfrt_table_data = bfruntime_pb2.TableData()
        for field_name, value in data.items():
            field = self.bfrt_info.get_data_field(table_name, field_name)
            bfrt_data_field = self.create_data_field(field.singleton, value)
            bfrt_table_data.fields.extend([bfrt_data_field])

        bfrt_table_entry.data.CopyFrom(bfrt_table_data)

        bfrt_update = bfrt_request.updates.add()
        bfrt_update.type = update_type
        bfrt_update.entity.table_entry.CopyFrom(bfrt_table_entry)

        return bfrt_request

    def create_table_read(self, program_name, table_name, key):
        bfrt_request = self.create_read_request(program_name)
        bfrt_table_entry = self.create_table_entry(table_name)
        bfrt_key_fields = self.create_key_fields(table_name, key)

        bfrt_table_entry.key.fields.extend(bfrt_key_fields)
        update = bfrt_request.entities.add()
        update.table_entry.CopyFrom(bfrt_table_entry)

        return bfrt_request

    def create_copy_to_cpu(self, program_name, port):
        """Create a for copying data to the CPU

        Warning:

            Experimental.
        """
        bfrt_request = self.create_write_request(program_name)
        bfrt_table_entry = self.create_table_entry("$pre.port")
        bfrt_key_field = self.create_key_field("$pre.port", "$DEV_PORT",
                                               Exact(port))
        bfrt_table_entry.extend([bfrt_key_field])

        info_cpu_port_field = self.bfrt_info.get_data_field(
            "$pre.port", "$COPY_TO_CPU_PORT_ENABLE"
        )
        bfrt_cpu_port_field = self.create_data_field(
            info_cpu_port_field.singleton, True
        )
        bfrt_table_entry.data.fields.extend([bfrt_cpu_port_field])

        bfrt_update = bfrt_request.updates.add()
        bfrt_update.type = bfruntime_pb2.Update.Type.MODIFY
        bfrt_update.entity.table_entry.CopyFrom(bfrt_table_entry)

    def create_set_pipeline_request(
        self, program_name, bfrt_path, context_path, binary_path
    ):

        # Need to figure out base_path properly later
        request = bfruntime_pb2.SetForwardingPipelineConfigRequest()
        request.client_id = self.client_id
        request.device_id = self.device_id
        request.base_path = f"install/share/tofinopd/{program_name}"
        request.action = (SetPipelineReq.VERIFY_AND_WARM_INIT_BEGIN_AND_END)

        config = request.config.add()
        config.p4_name = program_name
        config.bfruntime_info = open(bfrt_path, "rb").read()

        profile = config.profiles.add()
        profile.profile_name = "pipe"
        profile.context = open(context_path, "rb").read()
        profile.binary = open(binary_path, "rb").read()
        profile.pipe_scope.extend([0, 1, 2, 3])

        return request

    def create_get_pipeline_request(self):
        request = bfruntime_pb2.GetForwardingPipelineConfigRequest()
        request.device_id = self.device_id
        request.client_id = self.client_id
        return request


# def get_bfrt_data(self, stub, program_name=None):
#     request = bfruntime_pb2.GetForwardingPipelineConfigRequest()
#     request.device_id = self.device_id
#     request.client_id = self.client_id
#     response = stub.GetForwardingPipelineConfig(request)

#     if response is None:
#         raise Exception("Did not receive runtime info from device!")

#     if program_name is None:
#         program_name = response.config[0].p4_name
#     data = response.non_p4_config.bfruntime_info.decode("utf-8")
#     non_p4_config = json.loads(data)
#
#     p4_config = None
#
#     for config in response.config:
#         if program_name == config.p4_name:
#             p4_config = json.loads(config.bfruntime_info)
#             p4_config.get("tables").extend(non_p4_config.get("tables"))
#             return p4_config

#     return None
