'''    Copyright 2021 APS Networks GmbH

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
'''


def quoted(value):
    if isinstance(value, str):# or isinstance(value, unicode):
        return '\'{}\''.format(value)
    else:
        return value



class BfRtObject(object):
    def __repr__(self):
        pairs = []
        for key, value in self.__dict__.items():
            if value is not None:
                pairs.append( '{}={}'.format(key, quoted(value)))
        string = ', '.join(pairs)
        return '{}({})'.format(self.__class__.__name__, string)



class BfRtTable(BfRtObject):
    def __init__(self, id_, name, table_type, size):
        self.id = id_
        self.name = name
        self.table_type = table_type
        self.size = size
        self.key = []
        self.action_specs = []   
        self.data = []



class BfRtTableKey(BfRtObject):
    def __init__(self, 
            id_: int,
            name: str,
            repeated: bool,
            annotations: list,
            mandatory: bool,
            match_type: str,
            type_: dict):
        self.id = id_
        self.name = name
        self.repeated = repeated
        self.annotations = annotations
        self.mandatory = mandatory
        self.match_type = match_type
        self.type = type_



class BfRtTableActionSpec(BfRtObject):
    def __init__(self, id_: int, 
            name: str, 
            action_scope: str,
            annotations: list, 
            data: list):
        self.id = id_
        self.name = name
        self.action_scope = action_scope
        self.annotations = annotations
        self.data = data



class BfRtTableActionData(BfRtObject):
    def __init__(self, id_: int, 
            name: str,
            repeated: bool,
            mandatory: bool,
            read_only: bool,
            annotations: list,
            type_: dict):

        self.id = id_
        self.name = name
        self.repeated = repeated
        self.mandatory = mandatory
        self.read_only = read_only
        self.annotations = annotations
        self.type = type_



class BfRtTableDataFieldSingleton(BfRtObject):
    def __init__(self, 
            id_: int, 
            name: str, 
            repeated: bool, 
            annotations: list,
            type_: dict):
        self.id = id_
        self.name = name
        self.repeated = repeated
        self.annotations = annotations
        self.type = type_



class BfRtTableDataField(BfRtObject):
    def __init__(self,
            mandatory: bool,
            read_only: bool,
            singleton: BfRtTableDataFieldSingleton):
        self.mandatory = mandatory
        self.read_only = read_only
        self.singleton = singleton



def parse_table_key(key_data):
    id_ = key_data.get('id', None)
    name = key_data.get('name', None)
    repeated = key_data.get('repeated', None)
    annotations = key_data.get('annotations', None)
    mandatory = key_data.get('mandatory', None)
    match_type = key_data.get('match_type', None)
    type_ = key_data.get('type', None)

    return BfRtTableKey(id_=id_,
            name=name,
            repeated=repeated,
            annotations=annotations,
            mandatory=mandatory,
            match_type=match_type,
            type_=type_)



def parse_action_data(data):
    data_list = []
    for action in data:
        id_ = action.get('id', None)
        name = action.get('name', None)
        repeated = action.get('repeated', None)
        read_only = action.get('read_only', None)
        annotations = action.get('annotations', None)
        mandatory = action.get('mandatory', None)
        type_ = action.get('type', None)
        data_list.append(BfRtTableActionData(id_=id_,
                name=name,
                repeated=repeated,
                read_only=read_only,
                annotations=annotations,
                mandatory=mandatory,
                type_=type_))
    return data_list



def parse_action_spec(action_data):
    id_ = action_data.get('id', None)
    name = action_data.get('name', None)
    action_scope = action_data.get('action_scope', None)
    annotations = action_data.get('annotations', None)
    data = action_data.get('data', None)
    if data is not None:
        data = parse_action_data(data)

    return BfRtTableActionSpec(id_=id_,
            name=name,
            action_scope=action_scope,
            annotations=annotations,
            data=data)



def parse_table_data_field_singleton(singleton):
    id_ = singleton.get('id', None)
    name = singleton.get('name', None)
    repeated = singleton.get('repeated', None)
    annotations = singleton.get('annotations', None)
    type_ = singleton.get('type', None)

    return BfRtTableDataFieldSingleton(id_=id_,
            name=name,
            repeated=repeated,
            annotations=annotations,
            type_=type_)



def parse_table_data_field(field):
    mandatory = field.get('mandatory', None)
    read_only = field.get('read_only', None)
    singleton = field.get('singleton', None)
    if singleton is not None:
        singleton = parse_table_data_field_singleton(singleton)

    return BfRtTableDataField(mandatory=mandatory,
            read_only=read_only,
            singleton=singleton)



def parse_table(table_data):
    id_ = table_data.get('id', None)
    name = table_data.get('name', None)
    table_type = table_data.get('table_type', None)
    size = table_data.get('size', None)

    table = BfRtTable(id_, name, table_type, size)

    if 'key' in table_data:
        for key in table_data.get('key'):
            table.key.append(parse_table_key(key))

    if 'action_specs' in table_data:
        for action_spec in table_data.get('action_specs'):
            table.action_specs.append(parse_action_spec(action_spec))
            
    if 'data' in table_data:
        for field in table_data.get('data'):
            table.data.append(parse_table_data_field(field))

    return table



def parse_learn_filters(table_data):
    return None



class BfRtInfo(object):
    def __init__(self, data):
        if 'tables' in data:
            self.tables = []
            for table_data in data.get('tables'):
                self.tables.append(parse_table(table_data))
        if 'learn_filters' in data:
            self.learn_filters = []
            for table_data in data.get('learn_filters'):
                self.learn_filters.append(table_data)

    def get_action_field(self, table_name, action_name, field_name):
        action_spec = self.get_action_spec(table_name, action_name)
        if action_spec is not None:
            for field in action_spec.data:
                if field.name == field_name:
                    return field
        return None

    def get_action_field_id(self, table_name, action_name, field_name):
        field = self.get_action_field(table_name, action_name, field_name)
        if field is not None:
            return field.id
        return None

    def get_data_field(self, table_name, field_name):
        table = self.get_table(table_name)
        if table is not None:
            for field in table.data:
                if field.singleton != None:
                    if field.singleton.name == field_name:
                        return field
        return None

    def get_data_field_id(self, table_name, field_name):
        field = self.get_data_field(table_name, field_name)
        if field is not None:
            if field.singleton != None:
                return field.singleton.id
        return None

    def get_table(self, table_name):
        if 'tables' in self.__dict__:
            for table in self.tables:
                if table.name == table_name:
                    return table
        return None

    def get_key(self, table_name, key_name):
        table = self.get_table(table_name)
        if table is not None:
            for key in table.key:
                if key.name == key_name:
                    return key
        return None

    def get_table_id(self, table_name):
        table = self.get_table(table_name)
        if table is not None:
            return table.id
        return None

    def get_key_id(self, table_name, key_name):
        key = self.get_key(table_name, key_name)
        if key is not None:
            return key.id
        return None

    def get_action_spec(self, table_name, action_spec_name):
        table = self.get_table(table_name)
        if table is not None:
            for action_spec in table.action_specs:
                if action_spec.name == action_spec_name:
                    return action_spec

        return None

    def get_action_spec_id(self, table_name, action_spec_name):
        action_spec = self.get_action_spec(table_name, action_spec_name)
        if action_spec is not None:
            return action_spec.id
        return None








