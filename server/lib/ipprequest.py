#!/usr/bin/python

import sys

# various tags
zero_name_length                  = 0x00
operation_attributes_tag          = 0x01
job_attributes_tag                = 0x02
end_of_attributes_tag             = 0x03
printer_attributes_tag            = 0x04
unsupported_attributes_tag        = 0x05

# "out of band" value tags
oob_unsupported_value_tag         = 0x10
oob_default_value_tag             = 0x11
oob_unknown_value_tag             = 0x12
oob_no_value_tag                  = 0x13

# integer value tags
generic_integer_value_tag         = 0x20
integer_value_tag                 = 0x21
boolean_value_tag                 = 0x22
enum_value_tag                    = 0x23
                  
# octetString value tags
unspecified_octetString_value_tag = 0x30
dateTime_value_tag                = 0x31
resolution_value_tag              = 0x32
rangeOfInteger_value_tag          = 0x33
collection_value_tag              = 0x34
textWithLanguage_value_tag        = 0x35
nameWithLanguage_value_tag        = 0x36

# character-string value tags
generic_char_string_value_tag     = 0x40
textWithoutLanguage_value_tag     = 0x41
nameWithoutLanguage_value_tag     = 0x42
keyword_value_tag                 = 0x44
uri_value_tag                     = 0x45
uriScheme_value_tag               = 0x46
charset_value_tag                 = 0x47
naturalLanguage_value_tag         = 0x48
mimeMediaType_value_tag           = 0x49                                    

class IPPValue():
    """
    An IPP value consists of a tag and a value, and optionally, a name.
    """

    def __init__(self, value_tag, name, value):
        """
        Initialize an IPPValue:

        Arguments:

            value_tag -- one byte, identifying the type of value

            name -- (optional) variable size, identifying the name of
                    this value

            value -- variable size, containing the actual value
        """

        # make sure value_tag isn't empty
        assert value_tag is not None
        # make sure the size of value_tag is one byte
        assert sys.getsizeof(value_tag) == 1
        # make sure value isn't empty
        assert value is not None

        self.value_tag = value_tag
        self.name = name
        self.value = value

class IPPAttribute():
     """
     From RFC 2565:

     Each attribute consists of:
     -----------------------------------------------
     |                   value-tag                 |   1 byte
     -----------------------------------------------
     |               name-length  (value is u)     |   2 bytes
     -----------------------------------------------
     |                     name                    |   u bytes
     -----------------------------------------------
     |              value-length  (value is v)     |   2 bytes
     -----------------------------------------------
     |                     value                   |   v bytes
     -----------------------------------------------

     An additional value consists of:
     -----------------------------------------------------------
     |                   value-tag                 |   1 byte  |
     -----------------------------------------------           |
     |            name-length  (value is 0x0000)   |   2 bytes |
     -----------------------------------------------           |-0 or more
     |              value-length (value is w)      |   2 bytes |
     -----------------------------------------------           |
     |                     value                   |   w bytes |
     -----------------------------------------------------------
     """

     def __init__(self, attribute_tag, values):
         """
         Initialize an IPPAttribute.

         Arguments:

             attribute_tag -- one byte, identifying the type of attribute

             values -- a list of IPPValues.  May not be empty.
         """

         # make sure attribute_tag isn't empty
         assert attribute_tag is not None
         # make sure attribute_tag is of the right size
         assert sys.getsizeof(attribute_tag) == 1
         
         # make sure the list of values isn't empty
         assert len(values) > 0
         # make sure each value is an IPPValue
         for value in values: assert isinstance(value, IPPValue)
        
         self.attribute_tag = attribute_tag
         self.values = values

class IPPRequest():
    """
    From RFC 2565:
    
    The encoding for an operation request or response consists of:
    -----------------------------------------------
    |                  version-number             |   2 bytes  - required
    -----------------------------------------------
    |               operation-id (request)        |
    |                      or                     |   2 bytes  - required
    |               status-code (response)        |
    -----------------------------------------------
    |                   request-id                |   4 bytes  - required
    -----------------------------------------------------------
    |               xxx-attributes-tag            |   1 byte  |
    -----------------------------------------------           |-0 or more
    |             xxx-attribute-sequence          |   n bytes |
    -----------------------------------------------------------
    |              end-of-attributes-tag          |   1 byte   - required
    -----------------------------------------------
    |                     data                    |   q bytes  - optional
    -----------------------------------------------
    """

    # either give the version, operation_id, request_id,
    # attribute_sequence, and data, or a file handler (request) which
    # can be read from to get the request
    def __init__(self, version=None, operation_id=None, request_id=None, attributes=[], data=None, request=None):
        """
        Create an IPPRequest.  Takes either the segments of the
        request separately, or a file handle for the request to parse.
        If the file handle is passed in, all other arguments are
        ignored.

        Keyword arguments for passing in the segments of the request:
        
            version -- two bytes, identifying the version number of
                       the request
                            
            operation_id -- two bytes, identifying the id of the
                            requested operation

            request_id -- four bytes, identifying the id of the
                          request itself.

            attributes -- a list of IPPAttributes.  May be empty.

            data -- (optional) variable length, containing the actual
                    data of the request

        Keyword arguments for passing in the raw request:

            request -- a file handle that supports the read()
                       operation
        """

        if request is None:
            # make sure the version number isn't empty
            assert version is not None
            # make sure the version number is two bytes long
            assert sys.getsizeof(version) == 2
            # make sure the operation id isn't empty
            assert operation_id is not None
            # make sure the operation id is two bytes long
            assert sys.getsizeof(operation_id) == 2
            # make sure the request id isn't empty
            assert request_id is not None
            # make sure the request id is four bytes long
            assert sys.getsizeof(request_id) == 4
            
        # if the request isn't None, then we'll read directly from
        # that file handle
        if request is not None:
            # read the version-number (two bytes)
            self.version        = request.read(2)

            # read the operation-id (or status-code, but that's only
            # for a response) (two bytes)
            self.operation_id   = request.read(2)

            # read the request-id (4 bytes)
            self.request_id     = request.read(4)

            # now we have to read in the attributes.  Each attribute
            # has a tag (1 byte) and a sequence of values (n bytes)
            self.attributes     = []

            # read in the next byte
            next_byte = request.read(1)

            # as long as the next byte isn't signaling the end of the
            # attributes, keep looping and parsing attributes
            while next_byte != end_of_attributes_tag:
                
                # if the next byte is an attribute tag, then we're at
                # the start of a new attribute
                if next_byte <= 0x0F:

                    attribute_tag = next_byte
                    # read in the value tag (one byte)
                    value_tag     = request.read(1)
                    # read in the length of the name (two bytes)
                    name_length   = request.read(2)
                    # read the name (name_length bytes)
                    name          = request.read(name_length)
                    # read in the length of the value (two bytes)
                    value_length  = request.read(2)
                    # read in the value (value_length bytes)
                    value         = request.read(value_length)

                    # create a new IPPAttribute from the data we just
                    # read in, and add it to our attributes list
                    self.attributes.append(IPPAttribute(
                        attribute_tag,
                        [IPPValue(value_tag, name, value)]))

                # otherwise, we're still in the process of reading the
                # current attribute (now we'll read in another value)
                else:
                    
                    value_tag     = next_byte
                    # read in the length of the name (two bytes) --
                    # this should be 0x0
                    name_length   = request.read(2)
                    assert name_length == zero_name_length
                    # name should be empty
                    name          = None
                    # read in the length of the value (two bytes)
                    value_length  = request.read(2)
                    # read in the value (value_length bytes)
                    value         = request.read(value_length)

                    # add another value to the last attribute
                    self.attributes[-1].values.append(IPPValue(value_tag, name, value))

                # read another byte
                next_byte = request.read(1)

            # once we hit the end-of-attributes tag, the only thing
            # left is the data, so go ahead and read all of it
            self.data = request.read()

        # otherwise, just set the class variables to the keyword
        # arguments passed in
        else:
            self.version = version
            self.operation_id = operation_id
            self.request_id = request_id
            self.attributes = attributes
            self.data = data
