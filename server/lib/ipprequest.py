#!/usr/bin/python

import sys, struct, logging

# initialize logger
logger = logging.getLogger("ippLogger")

class IPPTags():
    """
    Contains constants for the various IPP tags, as defined by RFC
    2565.
    """
    
    # various tags
    ZERO_NAME_LENGTH                  = 0x00
    OPERATION_ATTRIBUTES_TAG          = 0x01
    JOB_ATTRIBUTES_TAG                = 0x02
    END_OF_ATTRIBUTES_TAG             = 0x03
    PRINTER_ATTRIBUTES_TAG            = 0x04
    UNSUPPORTED_ATTRIBUTES_TAG        = 0x05
    
    # "out of band" value tags
    UNSUPPORTED                       = 0x10
    DEFAULT                           = 0x11
    UNKNOWN                           = 0x12
    NO_VALUE                          = 0x13
    
    # integer value tags
    GENERIC_INTEGER                   = 0x20
    INTEGER                           = 0x21
    BOOLEAN                           = 0x22
    ENUM                              = 0x23

    # octetstring value tags
    UNSPECIFIED_OCTETSTRING           = 0x30
    DATETIME                          = 0x31
    RESOLUTION                        = 0x32
    RANGE_OF_INTEGER                  = 0x33
    COLLECTION                        = 0x34
    TEXT_WITH_LANGUAGE                = 0x35
    NAME_WITH_LANGUAGE                = 0x36

    # character-string value tags
    GENERIC_CHAR_STRING               = 0x40
    TEXT_WITHOUT_LANGUAGE             = 0x41
    NAME_WITHOUT_LANGUAGE             = 0x42
    KEYWORD                           = 0x44
    URI                               = 0x45
    URI_SCHEME                        = 0x46
    CHARSET                           = 0x47
    NATURAL_LANGUAGE                  = 0x48
    MIME_MEDIA_TYPE                   = 0x49                                    

class IPPValue():
    """
    An IPP value consists of a tag and a value, and optionally, a name.

    From RFC 2565:
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
    """

    def __init__(self, value_tag, value):
        """
        Initialize an IPPValue:

        Arguments:

            value_tag -- one byte, identifying the type of value

            value -- variable size, containing the actual value
        """

        # make sure value_tag isn't empty
        assert value_tag is not None
        # make sure value isn't empty
        assert value is not None

        self.value_tag = hex(value_tag)
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

    def __init__(self, name, values):
        """
        Initialize an IPPAttribute.
        
        Arguments:

        name -- the name of the attribute

        values -- a list of IPPValues.  May not be empty.
        """

        # make sure name isn't empty
        assert name is not None
         
        # make sure the list of values isn't empty
        assert len(values) > 0
        # make sure each value is an IPPValue
        for value in values: assert isinstance(value, IPPValue)
         
        self.name = str(name)
        self.values = values

    def toBinaryData(self):
        """
        Packs the attribute data into binary data.
        """

        # get the binary data for all the values
        values = []
        for v, i in zip(self.values, xrange(len(self.values))):
            if i == 0:
                name_length = sys.getsizeof(self.name)
                value_length = sys.getsizeof(v.value)
                values.append(struct.pack('>bh%ssh%ss' % (name_length, value_length),
                                          v.value_tag,
                                          name_length,
                                          self.name,
                                          value_length,
                                          v.value))
            else:
                value_length = sys.getsizeof(v.value)
                values.append(struct.pack('>bhh%ss' % (value_length),
                                          v.value_tag,
                                          name_length,
                                          value_length,
                                          v.value))
                
        # concatenate everything together and return it
        return ''.join(values)

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
            # make sure the operation id isn't empty
            assert operation_id is not None
            # make sure the request id isn't empty
            assert request_id is not None
            
        # if the request isn't None, then we'll read directly from
        # that file handle
        if request is not None:
            # read the version-number (two signed chars)
            self.version        = struct.unpack('>bb', request.read(2))
            logger.debug("version-number : (0x%X, 0x%X)" % self.version)

            # read the operation-id (or status-code, but that's only
            # for a response) (signed short)
            self.operation_id   = struct.unpack('>h', request.read(2))[0]
            logger.debug("operation-id : 0x%X" % self.operation_id)

            # read the request-id (signed int)
            self.request_id     = struct.unpack('>i', request.read(4))[0]
            logger.debug("request-id : 0x%X" % self.request_id)

            # now we have to read in the attributes.  Each attribute
            # has a tag (1 byte) and a sequence of values (n bytes)
            self.attributes     = []

            # read in the next byte
            next_byte = struct.unpack('>b', request.read(1))[0]
            logger.debug("next byte : 0x%X" % next_byte)

            # as long as the next byte isn't signaling the end of the
            # attributes, keep looping and parsing attributes
            while next_byte != IPPTags.END_OF_ATTRIBUTES_TAG:
                
                attribute_group_tag = next_byte
                logger.debug("attribute-tag : %i" % attribute_group_tag)

                next_byte = struct.unpack('>b', request.read(1))[0]
                logger.debug("next byte : 0x%X" % next_byte)

                while next_byte > 0x0F:
                    
                    # read in the value tag (signed char)
                    value_tag     = next_byte
                    logger.debug("value-tag : 0x%X" % value_tag)
                    
                    # read in the length of the name (signed short)
                    name_length   = struct.unpack('>h', request.read(2))[0]
                    logger.debug("name-length : %i" % name_length)
                    
                    if name_length != IPPTags.ZERO_NAME_LENGTH:
                        # read the name (a string of name_length bytes)
                        name          = request.read(name_length)
                        logger.debug("name : %s" % name)
                    
                        # read in the length of the value (signed short)
                        value_length  = struct.unpack('>h', request.read(2))[0]
                        logger.debug("value-length : %i" % value_length)
                    
                        # read in the value (string of value_length bytes)
                        value         = request.read(value_length)
                        logger.debug("value : %s" % value)

                        # create a new IPPAttribute from the data we just
                        # read in, and add it to our attributes list
                        self.attributes.append(IPPAttribute(name,
                                                            [IPPValue(value_tag, value)]))

                    else:
                        # read in the length of the value (signed short)
                        value_length  = struct.unpack('>h', request.read(2))[0]
                        logger.debug("value-length : %i" % value_length)
                    
                        # read in the value (string of value_length bytes)
                        value         = request.read(value_length)
                        logger.debug("value : %s" % value)

                        # add another value to the last attribute
                        self.attributes[-1].values.append(IPPValue(value_tag, value))

                    # read another byte
                    next_byte = struct.unpack('>b', request.read(1))[0]

            # once we hit the end-of-attributes tag, the only thing
            # left is the data, so go ahead and read all of it
            self.data = request.read()
            logger.debug("data : %s" % self.data)

        # otherwise, just set the class variables to the keyword
        # arguments passed in
        else:
            self.version = (int(version[0]), int(version[1]))
            self.operation_id = int(operation_id)
            self.request_id = int(request_id)
            self.attributes = attributes
            self.data = data

    def toBinaryData(self):
        """
        Packs the value data into binary data.
        """

        # convert the version, operation id, and request id to binary
        preattributes = struct.pack('>bbhi',
                                    self.version[0],
                                    self.version[1],
                                    self.operation_id,
                                    self.request_id)

        # convert the attributes to binary
        attributes = ''.join([a.toBinaryData() for a in self.attributes])

        # conver the end-of-attributes-tag to binary
        end_of_attributes_tag = struct.pack('>b', IPPTags.END_OF_ATTRIBUTES_TAG)

        # convert the data to binary
        if self.data is not None:
            data = ''.join([struct.pack('>b', x) for x in self.data])
        else:
            data = ''

        # append everything together and return it
        return preattributes + attributes + end_of_attributes_tag + data
