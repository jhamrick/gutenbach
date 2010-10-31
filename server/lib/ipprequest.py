#!/usr/bin/python

class IPPValue():
    def __init__(self, value_tag, name, value):
        assert value_tag is not None and \
               value is not None

        self.value_tag = value_tag
        self.name = name
        self.value = value

class IPPAttribute():
    # From RFC 2565:

    # Each attribute consists of:
    # -----------------------------------------------
    # |                   value-tag                 |   1 byte
    # -----------------------------------------------
    # |               name-length  (value is u)     |   2 bytes
    # -----------------------------------------------
    # |                     name                    |   u bytes
    # -----------------------------------------------
    # |              value-length  (value is v)     |   2 bytes
    # -----------------------------------------------
    # |                     value                   |   v bytes
    # -----------------------------------------------

    # An additional value consists of:
    # -----------------------------------------------------------
    # |                   value-tag                 |   1 byte  |
    # -----------------------------------------------           |
    # |            name-length  (value is 0x0000)   |   2 bytes |
    # -----------------------------------------------           |-0 or more
    # |              value-length (value is w)      |   2 bytes |
    # -----------------------------------------------           |
    # |                     value                   |   w bytes |
    # -----------------------------------------------------------

    def __init__(self, attribute_tag, values):
        assert attribute_tag is not None
        for value in values: assert isinstance(value, IPPValue)
        
        self.attribute_tag = attribute_tag
        self.values = values

class IPPRequest():
    # From RFC 2565:
    
    # The encoding for an operation request or response consists of:
    # -----------------------------------------------
    # |                  version-number             |   2 bytes  - required
    # -----------------------------------------------
    # |               operation-id (request)        |
    # |                      or                     |   2 bytes  - required
    # |               status-code (response)        |
    # -----------------------------------------------
    # |                   request-id                |   4 bytes  - required
    # -----------------------------------------------------------
    # |               xxx-attributes-tag            |   1 byte  |
    # -----------------------------------------------           |-0 or more
    # |             xxx-attribute-sequence          |   n bytes |
    # -----------------------------------------------------------
    # |              end-of-attributes-tag          |   1 byte   - required
    # -----------------------------------------------
    # |                     data                    |   q bytes  - optional
    # -----------------------------------------------

    # either give the version, operation_id, request_id,
    # attribute_sequence, and data, or a file handler (request) which
    # can be read from to get the request
    def __init__(self, version=None, operation_id=None, request_id=None, attributes=[], data=None, request=None):
        assert (version is not None and \
                operation_id is not None and \
                request_id is not None) or request is not None

        if request is not None:
            self.version        = request.read(2)
            self.operation_id   = request.read(2)
            self.request_id     = request.read(4)
            self.attributes     = []
            
            next_byte = request.read(1)
            while next_byte != 0x03:
                if next_byte <= 0x0F:
                    attribute_tag = next_byte
                    value_tag     = request.read(1)
                    name_length   = request.read(2)
                    name          = request.read(name_length)
                    value_length  = request.read(2)
                    value         = request.read(value_length)
                    
                    self.attributes.append(IPPAttribute(
                        attribute_tag,
                        [IPPValue(value_tag, name, value)]))
                else:
                    value_tag     = next_byte
                    name_length   = request.read(2)
                    name          = None
                    value_length  = request.read(2)
                    value         = request.read(value_length)
                    
                    self.attributes[-1].values.append(IPPValue(value_tag, name, value))
                    
                next_byte = request.read(1)

            self.data = request.read()

        else:
            self.version = version
            self.operation_id = operation_id
            self.request_id = request_id
            self.attributes = attributes
            self.data = data
