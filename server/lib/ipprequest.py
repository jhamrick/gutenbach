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

        self.value_tag = value_tag
        self.value = value

        # out-of-band value tags
        if self.value_tag == IPPTags.UNSUPPORTED or \
               self.value_tag == IPPTags.DEFAULT or \
               self.value_tag == IPPTags.UNKNOWN or \
               self.value_tag == IPPTags.NO_VALUE:
            self.value = ''

        # integer value tags
        elif self.value_tag == IPPTags.GENERIC_INTEGER:
            pass # not supported
        elif self.value_tag == IPPTags.INTEGER:
            self.value = struct.unpack('>i', value)[0]
        elif self.value_tag == IPPTags.BOOLEAN:
            self.value = struct.unpack('>?', value)[0]
        elif self.value_tag == IPPTags.ENUM:
            self.value = struct.unpack('>i', value)[0]

        # octet string value tags
        elif self.value_tag == IPPTags.UNSPECIFIED_OCTETSTRING:
            pass
        
        elif self.value_tag == IPPTags.DATETIME:
            # field  octets  contents                  range
            # -----  ------  --------                  -----
            #   1      1-2   year                      0..65536
            #   2       3    month                     1..12
            #   3       4    day                       1..31
            #   4       5    hour                      0..23
            #   5       6    minutes                   0..59
            #   6       7    seconds                   0..60
            #                (use 60 for leap-second)
            #   7       8    deci-seconds              0..9
            #   8       9    direction from UTC        '+' / '-'
            #   9      10    hours from UTC            0..11
            #  10      11    minutes from UTC          0..59

            self.value = struct.unpack('>hbbbbbbcbb', value)[0]
            
        elif self.value_tag == IPPTags.RESOLUTION:
            # OCTET-STRING consisting of nine octets of 2
            # SIGNED-INTEGERs followed by a SIGNED-BYTE. The first
            # SIGNED-INTEGER contains the value of cross feed
            # direction resolution. The second SIGNED-INTEGER contains
            # the value of feed direction resolution. The SIGNED-BYTE
            # contains the units

            self.value = struct.unpack('>iib', value)
            
        elif self.value_tag == IPPTags.RANGE_OF_INTEGER:
            # Eight octets consisting of 2 SIGNED-INTEGERs.  The first
            # SIGNED-INTEGER contains the lower bound and the second
            # SIGNED-INTEGER contains the upper bound.

            self.value = struct.unpack('>ii', value)

        elif self.value_tag == IPPTags.TEXT_WITH_LANGUAGE or \
                 self.value_tag == IPPTags.NAME_WITH_LANGUAGE:
            a = struct.unpack('>h', value[:2])[0]
            b = struct.unpack('>%ss' % a, value[2:a+2])[0]
            c = struct.unpack('>h', value[a+2:a+4])[0]
            d = struct.unpack('>%ss' % c, value[a+4:][0])
            self.value = (a, b, c, d)

        # character string value tags
        elif self.value_tag == IPPTags.TEXT_WITHOUT_LANGUAGE or \
                 self.value_tag == IPPTags.NAME_WITHOUT_LANGUAGE:
            self.value = str(value)
        elif self.value_tag == IPPTags.GENERIC_CHAR_STRING or \
                 self.value_tag == IPPTags.KEYWORD or \
                 self.value_tag == IPPTags.URI or \
                 self.value_tag == IPPTags.URI_SCHEME or \
                 self.value_tag == IPPTags.CHARSET or \
                 self.value_tag == IPPTags.NATURAL_LANGUAGE or \
                 self.value_tag == IPPTags.MIME_MEDIA_TYPE:
            self.value = str(value)

    def valueToBinary(self):

        # out-of-band value tags
        if self.value_tag == IPPTags.UNSUPPORTED or \
               self.value_tag == IPPTags.DEFAULT or \
               self.value_tag == IPPTags.UNKNOWN or \
               self.value_tag == IPPTags.NO_VALUE:
            return (0, '')

        # integer value tags
        elif self.value_tag == IPPTags.GENERIC_INTEGER:
            pass
        elif self.value_tag == IPPTags.INTEGER:
            return (4, struct.pack('>i', self.value))
        elif self.value_tag == IPPTags.BOOLEAN:
            return (1, struct.pack('>?', self.value))
        elif self.value_tag == IPPTags.ENUM:
            return (4, struct.pack('>i', self.value))

        # octet string value tags
        elif self.value_tag == IPPTags.UNSPECIFIED_OCTETSTRING:
            pass
        elif self.value_tag == IPPTags.DATETIME:
            # field  octets  contents                  range
            # -----  ------  --------                  -----
            #   1      1-2   year                      0..65536
            #   2       3    month                     1..12
            #   3       4    day                       1..31
            #   4       5    hour                      0..23
            #   5       6    minutes                   0..59
            #   6       7    seconds                   0..60
            #                (use 60 for leap-second)
            #   7       8    deci-seconds              0..9
            #   8       9    direction from UTC        '+' / '-'
            #   9      10    hours from UTC            0..11
            #  10      11    minutes from UTC          0..59
            
            return (11, struct.pack('>hbbbbbbcbb', self.value))
            
        elif self.value_tag == IPPTags.RESOLUTION:
            # OCTET-STRING consisting of nine octets of 2
            # SIGNED-INTEGERs followed by a SIGNED-BYTE. The first
            # SIGNED-INTEGER contains the value of cross feed
            # direction resolution. The second SIGNED-INTEGER contains
            # the value of feed direction resolution. The SIGNED-BYTE
            # contains the units
            
            return (9, struct.pack('>iib', self.value))
            
        elif self.value_tag == IPPTags.RANGE_OF_INTEGER:
            # Eight octets consisting of 2 SIGNED-INTEGERs.  The first
            # SIGNED-INTEGER contains the lower bound and the second
            # SIGNED-INTEGER contains the upper bound.
            
            return (8, struct.pack('>ii', self.value))

        elif self.value_tag == IPPTags.TEXT_WITH_LANGUAGE or \
                 self.value_tag == IPPTags.NAME_WITH_LANGUAGE:
            a_bin = struct.pack('>h', self.value[0])
            b_bin = struct.pack('>%ss' % self.value[0], self.value[1])
            c_bin = struct.pack('>h', self.value[2])
            d_bin = struct.pack('>%ss' % self.value[2], self.value[3])
            return (4 + self.value[0] + self.value[2],
                    a_bin + b_bin + c_bin + d_bin)

        # character string value tags
        elif self.value_tag == IPPTags.TEXT_WITHOUT_LANGUAGE or \
                 self.value_tag == IPPTags.NAME_WITHOUT_LANGUAGE:
            return (len(self.value), struct.pack('>%ss' % len(self.value), self.value))
        elif self.value_tag == IPPTags.GENERIC_CHAR_STRING or \
                 self.value_tag == IPPTags.KEYWORD or \
                 self.value_tag == IPPTags.URI or \
                 self.value_tag == IPPTags.URI_SCHEME or \
                 self.value_tag == IPPTags.CHARSET or \
                 self.value_tag == IPPTags.NATURAL_LANGUAGE or \
                 self.value_tag == IPPTags.MIME_MEDIA_TYPE:
            return (len(self.value), struct.pack('>%ss' % len(self.value), self.value))

        return len(self.value), self.value

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
         
        self.name = name
        self.values = values

    def toBinaryData(self):
        """
        Packs the attribute data into binary data.
        """

        # get the binary data for all the values
        values = []
        for v, i in zip(self.values, xrange(len(self.values))):

            # get the name length (0 for everything but the first
            # value)
            if i == 0:
                name_length = len(self.name)
            else:
                name_length = 0

            # get the value length and binary value
            value_length, value_bin = v.valueToBinary()

            logger.debug("dumping name_length : %i" % name_length)
            logger.debug("dumping name : %s" % self.name)
            logger.debug("dumping value_length : %i" % value_length)
            logger.debug("dumping value : %s" % v.value)

            # the value tag in binary
            value_tag_bin = struct.pack('>b', v.value_tag)

            # the name length in binary
            name_length_bin = struct.pack('>h', name_length)

            # the name in binary
            name_bin = self.name

            # the value length in binary
            value_length_bin = struct.pack('>h', value_length)

            if i == 0:
                values.append(''.join([value_tag_bin,
                                       name_length_bin,
                                       name_bin,
                                       value_length_bin,
                                       value_bin]))
            else:
                values.append(''.join([value_tag_bin,
                                       name_length_bin,
                                       value_length_bin,
                                       value_bin]))
                
        # concatenate everything together and return it
        return ''.join(values)

class IPPAttributeGroup():
    """
    An IPPAttributeGroup consists of an attribute-group-tag, followed
    by a sequence of IPPAttributes.
    """

    def __init__(self, attribute_group_tag, attributes=[]):
        """
        Initialize an IPPAttributeGroup.

        Arguments:

            attribute_group_tag -- a signed char, holds the tag of the
                                   attribute group

            attributes -- (optional) a list of attributes
        """

        # make sure attribute_group_tag isn't empty
        assert attribute_group_tag is not None

        # make sure attributes is a list or tuple of IPPAttributes
        assert isinstance(attributes, (list, tuple))
        for a in attributes: assert isinstance(a, IPPAttribute)

        self.attribute_group_tag = attribute_group_tag
        self.attributes = attributes

    def toBinaryData(self):
        """
        Convert the IPPAttributeGroup to binary.
        """

        # conver the attribute_group_tag to binary
        tag = struct.pack('>b', self.attribute_group_tag)

        # convert each of the attributes to binary
        attributes = [a.toBinaryData() for a in self.attributes]

        # concatenate everything and return
        return tag + ''.join(attributes)

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
    def __init__(self, version=None, operation_id=None, request_id=None,
                 attribute_groups=[], data=None, request=None, length=sys.maxint):
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

            attribute_groups -- a list of IPPAttributes, at least length 1

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
            # make sure attribute_groups is a list of IPPAttributes
            assert len(attribute_groups) > 0
            for a in attribute_groups: assert isinstance(a, IPPAttribute)
            
        # if the request isn't None, then we'll read directly from
        # that file handle
        if request is not None:
            # read the version-number (two signed chars)
            self.version        = struct.unpack('>bb', request.read(2))
            length -= 2
            logger.debug("version-number : (0x%X, 0x%X)" % self.version)

            # read the operation-id (or status-code, but that's only
            # for a response) (signed short)
            self.operation_id   = struct.unpack('>h', request.read(2))[0]
            length -= 2
            logger.debug("operation-id : 0x%X" % self.operation_id)

            # read the request-id (signed int)
            self.request_id     = struct.unpack('>i', request.read(4))[0]
            length -= 4
            logger.debug("request-id : 0x%X" % self.request_id)

            # now we have to read in the attributes.  Each attribute
            # has a tag (1 byte) and a sequence of values (n bytes)
            self.attribute_groups = []

            # read in the next byte
            next_byte = struct.unpack('>b', request.read(1))[0]
            length -=1
            logger.debug("next byte : 0x%X" % next_byte)

            # as long as the next byte isn't signaling the end of the
            # attributes, keep looping and parsing attributes
            while next_byte != IPPTags.END_OF_ATTRIBUTES_TAG:
                
                attribute_group_tag = next_byte
                logger.debug("attribute-tag : %i" % attribute_group_tag)

                attributes = []

                next_byte = struct.unpack('>b', request.read(1))[0]
                length -= 1
                logger.debug("next byte : 0x%X" % next_byte)

                while next_byte > 0x0F:
                    
                    # read in the value tag (signed char)
                    value_tag     = next_byte
                    logger.debug("value-tag : 0x%X" % value_tag)
                    
                    # read in the length of the name (signed short)
                    name_length   = struct.unpack('>h', request.read(2))[0]
                    length -= 2
                    logger.debug("name-length : %i" % name_length)
                    
                    if name_length != IPPTags.ZERO_NAME_LENGTH:
                        # read the name (a string of name_length bytes)
                        name          = request.read(name_length)
                        length -= name_length
                        logger.debug("name : %s" % name)
                    
                        # read in the length of the value (signed short)
                        value_length  = struct.unpack('>h', request.read(2))[0]
                        length -= 2
                        logger.debug("value-length : %i" % value_length)
                    
                        # read in the value (string of value_length bytes)
                        value         = request.read(value_length)
                        length -= value_length
                        
                        ippvalue = IPPValue(value_tag, value)
                        logger.debug("value : %s" % ippvalue.value)

                        # create a new IPPAttribute from the data we just
                        # read in, and add it to our attributes list
                        attributes.append(IPPAttribute(name, [ippvalue]))

                    else:
                        # read in the length of the value (signed short)
                        value_length  = struct.unpack('>h', request.read(2))[0]
                        length -= 2
                        logger.debug("value-length : %i" % value_length)
                    
                        # read in the value (string of value_length bytes)
                        value         = request.read(value_length)
                        length -= value_length

                        ippvalue = IPPValue(value_tag, value)
                        logger.debug("value : %s" % ippvalue.value)

                        # add another value to the last attribute
                        attributes[-1].values.append(ippvalue)

                    # read another byte
                    next_byte = struct.unpack('>b', request.read(1))[0]
                    length -= 1

                self.attribute_groups.append(IPPAttributeGroup(attribute_group_tag, attributes))

            # once we hit the end-of-attributes tag, the only thing
            # left is the data, so go ahead and read all of it
            assert length >= 0
            self.data = request.read(length)
            logger.debug("data : %s" % self.data)

        # otherwise, just set the class variables to the keyword
        # arguments passed in
        else:
            self.version = (version[0], version[1])
            self.operation_id = operation_id
            self.request_id = request_id
            self.attribute_groups = attribute_groups
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

        # convert the attribute groups to binary
        attribute_groups = ''.join([a.toBinaryData() for a in self.attribute_groups])

        # conver the end-of-attributes-tag to binary
        end_of_attributes_tag = struct.pack('>b', IPPTags.END_OF_ATTRIBUTES_TAG)

        # convert the data to binary
        if self.data is not None:
            data = ''.join([struct.pack('>b', x) for x in self.data])
        else:
            data = ''

        # append everything together and return it
        return preattributes + attribute_groups + end_of_attributes_tag + data
