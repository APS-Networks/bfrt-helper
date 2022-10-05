import bfrt_helper.pb2.bfruntime_pb2 as bfruntime_pb2
from bfrt_helper.pb2.bfruntime_pb2 import WriteRequest
from bfrt_helper.pb2.bfruntime_pb2 import Update

# Atomicity = WriteRequest.Atomicity

from bfrt_helper.pb2.bfruntime_pb2 import (
    SetForwardingPipelineConfigRequest as SetPipelineReq,
)

from bfrt_helper.match import Exact
from bfrt_helper.match import LongestPrefixMatch
from bfrt_helper.match import Ternary
from bfrt_helper.fields import Field, DevPort


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

    def __init__(self, table_name: str, action_name: str, param_name: str):
        msg = (
            "Could not find action parameter ",
            f"{table_name}::{action_name}::{param_name}",
        )
        super().__init__(msg)


class UnknownTable(Exception):
    """Exception raised when a given table could not be found.

    Args:
        table_name (str): String containing the name of the table.
    """

    def __init__(self, table_name: str):
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

    def __init__(self, table_name: str, field_name: str):
        super().__init__(f"Could not find key field {table_name}::{field_name}")


class MismatchedMatchType(Exception):
    """Exception raised when the match for a key field declared in a request
    does not match that which is defined in the table.

    The current accepted match types are:

        * :py:class:`LongestPrefixMatch`
        * :py:class:`Exact`
        * :py:class:`Ternary`

    Args:
        field_name (str): The name of the field in question.
        field_data (Field): The instance of the incorrect field.
        expected (str): The name of the expected data type.
    """

    def __init__(self, field_name: str, field_data: Field, expected: str):
        clz = field_data.__class__.__name__
        msg = (
            f"Expected field type for {field_name} is {expected}, but have ",
            f"{clz}",
        )
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

    def __init__(self, expected: int, observed: int):
        msg = f"Expected data size {expected} but have {observed}"
        super().__init__(msg)


class InvalidActionParameter(Exception):
    def __init__(self, table_name: str, action_name: str, param_name: str, reason: str):
        msg = f"{table_name}::{action_name}::{param_name}: {reason}"
        super().__init__(msg)


class BfRtHelper:
    """Barefoot Runtime gRPC Helper Class"""

    def __init__(self, device_id, client_id, bfrt_info):
        self.device_id = device_id
        self.client_id = client_id
        self.bfrt_info = bfrt_info

    def create_subscribe_request(
        self,
        learn: bool = True,  # Receive learn notifications
        timeout: bool = True,  # Receive timeout notifications
        port_change: bool = True,  # Receive port state change notifications
        request_timeout: int = 10,  # Subscribe response timeout
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
        program_name: str,
        atomicity=WriteRequest.Atomicity.CONTINUE_ON_ERROR,
        target: dict = {},
    ):
        """Creates a basic write request with no updates.

        This creates the base gRPC object for the majority of runtime program
        manipulation.

        The optional target parameter contains any of the following:

        * ``pipe_id`` : The id of the pipe to apply the write. Tofino devices
          may contain multiple "pipes", which in turn are comprised of
          multiple ports. Each pipe is capable of being loaded with it's own
          P4 program that acts independently from other pipes. An ID is
          therefore necessary to identify it.
        * ``direction``: The Tofino Native Architecture has a concept of ingress
          and egress pipelines. It is possible (AFAWK) that a single control
          can be associated with both ingress and egress pipelines, but their
          "instantiation" will contain tables unique to the direction.
        * ``prsr_id``: TODO

        The default argument for this is equivalent to:

        .. code:: python

            {
                'pipe_id': 0xFFFF, # All pipes
                'direction': 0xFF, # All directions
                'prsr_id': 0xFF # TODO
            }

        Args:

            program_name (str): The name of the program to target.

            atomicity (WriteRequest.Atomicity): Controls the behaviour of a
                write request with respect to batched updates, i.e., whether
                any errors are ignored, errors cause rollbacks of previously
                submitted writes in the batch, or whether the write is treated
                as a single atomic transaction.

            target (dict): An optionally provided dictionary that maps parser
                identifier information.

        Returns:

            bfruntime_pb2.WriteRequest
        """
        request = bfruntime_pb2.WriteRequest()
        request.client_id = self.client_id
        request.p4_name = program_name
        request.atomicity = atomicity

        device = bfruntime_pb2.TargetDevice()
        device.device_id = self.device_id
        device.pipe_id = target.get("pipe_id", 0xFFFF)
        device.direction = target.get("direction", 0xFF)
        device.prsr_id = target.get("prsr_id", 0xFF)

        request.target.CopyFrom(device)

        return request

    def create_read_request(self, program_name: str):
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

    def create_table_entry(self, table_name: str):
        """Generates empty table message

        This produces the base gRPC object for a table entry for the supplied
        table name.

        Args:

            table_name (str): Name of table to target

        Returns:

            bfruntime_pb2.TableEntry

        """
        table_id = self.bfrt_info.get_table_id(table_name)
        if table_id is None:
            raise UnknownTable(table_name)
        table_entry = bfruntime_pb2.TableEntry()
        table_entry.table_id = table_id

        return table_entry

    def create_key_field(self, table_name: str, field_name: str, data: Field):
        """Generates key field component of a gRPC message

        The performs a lookup of the key id (as messages contain a table ID and
        not the name) using the :py:class:`BfRtInfo` object and also type checks
        the match type.

        Args:

            table_name (str): Name of table to target

            field_name (str): Name of specific key field

            data (Field): Field data supplied as in instance of a `Field`
                object.

        Returns:

            bfruntime_pb2.KeyField

        Raises:

            UnknownKeyField: If the :py:class:`BfRtInfo` object did not contain a
                a valid key field for the given table and field names.

            MismatchedMatchType: If the match types (e.g. :py:class:`Exact`) does not
                match the match type defined for the field actually present in
                the table.
        """
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
                    raise MismatchedDataSize(field.type["width"], value.bitwidth)
            elif field.type["type"] == "uint16":
                if value.bitwidth != 16:
                    raise MismatchedDataSize(field.type["width"], value.bitwidth)
            elif field.type["type"] == "uint32":
                if value.bitwidth != 32:
                    raise MismatchedDataSize(field.type["width"], value.bitwidth)
            data_field.stream = value.to_bytes()
        elif isinstance(value, float):
            data_field.float_val = value
        elif isinstance(value, str):
            if 'choices' in field.type:
                choices = field.type['choices']
                if value not in choices:
                    raise Exception(f'String value {value} not in choices: {choices}')

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
        """Create the key fields gRPC message component"""
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
                    raise UnknownActionParameter(table_name, action_name, param_name)

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
        update_type=Update.Type.INSERT,  # Type not documented here because it
        # absolutely destroys generated docs.
    ):
        """Create a match-action table write request

        .. note::

            This does not support batched writes.

        Args:
            program_name (str): Name of program to target.

            table_name (str): Name of table within the program. Depending on how
                the program has been compiled, you may need to prefix this name
                with "pipe", e.g. "pipe.IngressControl.table".

            key (dict): Dictionary of match field names to their match. The keys
                should be strings, and the value should be an instance of a
                :py:class:`Match` (e.g. :py:class:`Exact`) constructed with the correct
                field type as defined in the program.

            action_name (str): Name of the action to execute on a match.

            action_params (dict): Dictionary of parameter names and their values
                to pass to the executed action. As before, the key should be a
                string, but the value should derive from :py:class:`Field`.

            update_type (Update.Type): The type of operation to take place,
                e.g., INSERT, MODIFY, DELETE. The default value of ``1``
                corresponds to Update.Type.INSERT.

        """
        bfrt_request = self.create_write_request(program_name)
        bfrt_table_entry = self.create_table_entry(table_name)
        bfrt_key_fields = self.create_key_fields(table_name, key)
        bfrt_table_entry.key.fields.extend(bfrt_key_fields)

        if action_name is not None:
            bfrt_action = self.create_action(table_name, action_name, action_params)
            bfrt_table_entry.data.CopyFrom(bfrt_action)

        bfrt_update = bfrt_request.updates.add()
        bfrt_update.type = update_type
        bfrt_update.entity.table_entry.CopyFrom(bfrt_table_entry)

        return bfrt_request

    def create_table_data_write(
        self,
        program_name: str,
        table_name,
        key,
        data,
        update_type=bfruntime_pb2.Update.Type.INSERT,
    ):
        """Create a table write for arbitrary tables.

        It is possible to write to many other tables exposed to the runtime
        interface which can be used to manipulate copy to cpu settings,
        multicast groups, port settings etc.

        While these tables can be considered as "ordinary" database tables,
        they are still manipulated by the same mechanisms as a match-action
        update.

        .. note::

            This does not support batched writes.

        Args:
            program_name (str): Name of program to target.

            table_name (str): Name of table within the program. Depending on how
                the program has been compiled, you may need to prefix this name
                with "pipe", e.g. "pipe.IngressControl.table".

            key (dict): Dictionary of match field names to their match. The keys
                should be strings, and the value should be an instance of a
                :py:class:`Match` (e.g. :py:class:`Exact`) constructed with the correct
                field type as defined in the program.

            data (Field): The data to be added to the table. Like match-action
                updates, this can be expressed handily with a :py:class:`Field`.
                This may could involve a :py:class:`StringField`, however a use case
                for this hasn't been firmly established.

            update_type (Update.Type): The type of operation to take place,
                e.g., INSERT, MODIFY, DELETE. The default value of ``1``
                corresponds to Update.Type.INSERT.
        """
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
                                               Exact(DevPort(port)))
        bfrt_table_entry.key.fields.extend([bfrt_key_field])

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

        return bfrt_request

    def create_set_pipeline_request(
        self, program_name, bfrt_path, context_path, binary_path
    ):

        # Need to figure out base_path properly later
        request = bfruntime_pb2.SetForwardingPipelineConfigRequest()
        request.client_id = self.client_id
        request.device_id = self.device_id
        request.base_path = f"install/share/tofinopd/"
        request.action = SetPipelineReq.VERIFY_AND_WARM_INIT_BEGIN_AND_END

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



import json

from bfrt_helper.fields import StringField
from bfrt_helper.bfrt_info import BfRtInfo
from bfrt_helper.bfrt import BfRtHelper


def make_bfrt_helper(host, device_id, client_id, bfrt_path):
    """ Create a BfRtHelper instance with BfRtInfo already loaded. """
    bfrt_data = json.loads(open(bfrt_path).read())
    bfrt_info = BfRtInfo(bfrt_data)
    return BfRtHelper(device_id, client_id, bfrt_info)



def make_empty_bfrt_helper(device_id, client_id):
    """ Make an empty BfRtInfo object """
    bfrt_info = BfRtInfo({})
    return BfRtHelper(device_id, client_id, bfrt_info)


def make_merged_config(response):
    """ Create a merged jSON configuration

    This creates a merged jSON configuration from a BfRt response containing
    both program and internal non-p4 data.
    """
    non_p4_data = response.non_p4_config.bfruntime_info.decode('utf-8')
    non_p4_config = json.loads(non_p4_data)

    configs = []

    for config in response.config:
        p4_config = json.loads(config.bfruntime_info)
        p4_config.get('tables').extend(non_p4_config.get('tables'))
        configs.append(p4_config)

    return configs
    

def make_port_map(program_name, bfrt_helper, client, ports):
    """ Create a map of port to device port

    For a given set of input ports, this will request over gRPC the device port
    information.
    """
    request = bfrt_helper.create_read_request(program_name)
    for port in ports:
        table_entry = bfrt_helper.create_table_entry('$PORT_STR_INFO')
        key_field = bfrt_helper.create_key_fields('$PORT_STR_INFO',
            key_fields={
                '$PORT_NAME': Exact(StringField(port))
            })
        table_entry.key.fields.extend(key_field)
        update = request.entities.add()
        update.table_entry.CopyFrom(table_entry)

    response = client.Read(request)

    data = response.next()

    result = {}
    for entity in data.entities:
       port_name = entity.table_entry.key.fields[0].exact.value.decode('utf-8')
       dev_port = entity.table_entry.data.fields[0].stream
       dev_port = int.from_bytes(dev_port, byteorder='big')
       result[port_name] = dev_port
    
    return result