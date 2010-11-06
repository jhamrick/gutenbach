#!/usr/bin/python

import sys, struct

class IPPTags():
    """
    Contains constants for the various IPP tags, as defined by RFC
    2565.
    """
    
    # various tags
    ZERO_NAME_LENGTH                  = 0X00
    OPERATION_ATTRIBUTES_TAG          = 0X01
    JOB_ATTRIBUTES_TAG                = 0X02
    END_OF_ATTRIBUTES_TAG             = 0X03
    PRINTER_ATTRIBUTES_TAG            = 0X04
    UNSUPPORTED_ATTRIBUTES_TAG        = 0X05
    
    # "out of band" value tags
    UNSUPPORTED                       = 0X10
    DEFAULT                           = 0X11
    UNKNOWN                           = 0X12
    NO_VALUE                          = 0X13
    
    # integer value tags
    GENERIC_INTEGER                   = 0X20
    INTEGER                           = 0X21
    BOOLEAN                           = 0X22
    ENUM                              = 0X23

    # octetstring value tags
    UNSPECIFIED_OCTETSTRING           = 0X30
    DATETIME                          = 0X31
    RESOLUTION                        = 0X32
    RANGEOFINTEGER                    = 0X33
    COLLECTION                        = 0X34
    TEXTWITHLANGUAGE                  = 0X35
    NAMEWITHLANGUAGE                  = 0X36

    # character-string value tags
    GENERIC_CHAR_STRING               = 0X40
    TEXTWITHOUTLANGUAGE               = 0X41
    NAMEWITHOUTLANGUAGE               = 0X42
    KEYWORD                           = 0X44
    URI                               = 0X45
    URISCHEME                         = 0X46
    CHARSET                           = 0X47
    NATURALLANGUAGE                   = 0X48
    MIMEMEDIATYPE                     = 0X49                                    

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

        self.value_tag = hex(value_tag)
        self.name = str(name)
        self.value = str(value)

class IPPAttribute():
     """
     In addition to what the RFC reports, an attribute has an
     'attribute tag', which specifies what type of attribute it is.
     It is 1 bytes long, and comes before the list of values.

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
        
         self.attribute_tag = hex(attribute_tag)
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
        
            version -- a tuple of two signed chars, identifying the
                       major version and minor version numbers of the
                       request
                            
            operation_id -- a signed short, identifying the id of the
                            requested operation

            request_id -- a signed int, identifying the id of the
                          request itself.

            attributes -- (optional) a list of IPPAttributes

            data -- (optional) variable length, containing the actual
                    data of the request

        Keyword arguments for passing in the raw request:

            request -- a file handle that supports the read()
                       operation
        """

        if request is None:
            # make sure the version number isn't empty
            assert version is not None
            # make sure verison is a tuple of length 2
            assert isinstance(version, tuple)
            assert len(version) == 2
            # make sure the major version number is one byte long
            assert sys.getsizeof(version[0]) == 1
            # make sure the minor version number is one byte long
            assert sys.getsizeof(version[1]) == 1
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
            # read the version-number (two signed chars)
            self.version        = struct.unpack('bb', request.read(2))

            # read the operation-id (or status-code, but that's only
            # for a response) (signed short)
            self.operation_id   = struct.unpack('h', request.read(2))

            # read the request-id (signed int)
            self.request_id     = struct.unpack('i', request.read(4))

            # now we have to read in the attributes.  Each attribute
            # has a tag (1 byte) and a sequence of values (n bytes)
            self.attributes     = []

            # read in the next byte
            next_byte = struct.unpack('b', request.read(1))

            # as long as the next byte isn't signaling the end of the
            # attributes, keep looping and parsing attributes
            while next_byte != IPPTags.END_OF_ATTRIBUTES_TAG:
                
                # if the next byte is an attribute tag, then we're at
                # the start of a new attribute
                if next_byte <= 0x0F:

                    attribute_tag = next_byte
                    # read in the value tag (signed char)
                    value_tag     = struct.unpack('b', request.read(1))
                    # read in the length of the name (signed short)
                    name_length   = struct.unpack('h', request.read(2))
                    # read the name (a string of name_length bytes)
                    name          = struct.unpack('s', request.read(name_length))
                    # read in the length of the value (signed short)
                    value_length  = struct.unpack('h', request.read(2))
                    # read in the value (string of value_length bytes)
                    value         = struct.unpack('b'*value_length, request.read(value_length))

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
                    name_length   = struct.unpack('h', request.read(2))
                    assert name_length == zero_name_length
                    # name should be empty
                    name          = ''
                    # read in the length of the value (two bytes)
                    value_length  = struct.unpack('h', request.read(2))
                    # read in the value (value_length bytes)
                    value         = struct.unpack('b'*value_length, request.read(value_length))

                    # add another value to the last attribute
                    self.attributes[-1].values.append(IPPValue(value_tag, name, value))

                # read another byte
                next_byte = struct.unpack('b', request.read(1))

            # once we hit the end-of-attributes tag, the only thing
            # left is the data, so go ahead and read all of it
            buff = request.read()
            self.data = struct.unpack('b'*len(buff), sys.getsizeof(buff))

        # otherwise, just set the class variables to the keyword
        # arguments passed in
        else:
            self.version = int(version)
            self.operation_id = int(operation_id)
            self.request_id = int(request_id)
            self.attributes = attributes
            self.data = data
