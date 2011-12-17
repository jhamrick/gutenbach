from .attribute import Attribute
from .attributegroup import AttributeGroup
from .constants import AttributeTags
from .value import Value
import sys
import struct
import logging

# initialize logger
logger = logging.getLogger(__name__)

class Request():
    """From RFC 2565:
    
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
        """Create a Request.  Takes either the segments of the request
        separately, or a file handle for the request to parse.  If the
        file handle is passed in, all other arguments are ignored.

        Keyword arguments for passing in the segments of the request:
        
            version -- a tuple of two signed chars, identifying the
                       major version and minor version numbers of the
                       request
                            
            operation_id -- a signed short, identifying the id of the
                            requested operation

            request_id -- a signed int, identifying the id of the
                          request itself.

            attribute_groups -- a list of Attributes, at least length 1

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
            # make sure attribute_groups is a list of Attributes
            for a in attribute_groups: assert isinstance(a, AttributeGroup)
            
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
            while next_byte != AttributeTags.END:
                
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
                    
                    if name_length != AttributeTags.ZERO_NAME_LENGTH:
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
                        
                        ippvalue = Value.unpack(value_tag, value)
                        logger.debug("value : %s" % ippvalue.value)

                        # create a new Attribute from the data we just
                        # read in, and add it to our attributes list
                        attributes.append(Attribute(name, [ippvalue]))

                    else:
                        # read in the length of the value (signed short)
                        value_length  = struct.unpack('>h', request.read(2))[0]
                        length -= 2
                        logger.debug("value-length : %i" % value_length)
                    
                        # read in the value (string of value_length bytes)
                        value         = request.read(value_length)
                        length -= value_length

                        ippvalue = Value.unpack(value_tag, value)
                        logger.debug("value : %s" % ippvalue.value)

                        # add another value to the last attribute
                        attributes[-1].values.append(ippvalue)

                    # read another byte
                    next_byte = struct.unpack('>b', request.read(1))[0]
                    length -= 1

                self.attribute_groups.append(AttributeGroup(
                    attribute_group_tag, attributes))

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

    def getAttributeGroup(self, tag):
        return filter(lambda x: x.attribute_group_tag == tag,
                      self.attribute_groups)

    @property
    def packed_value(self):
        """Packs the value data into binary data.
        
        """

        # make sure the version number isn't empty
        assert self.version is not None
        # make sure verison is a tuple of length 2
        assert isinstance(self.version, tuple)
        assert len(self.version) == 2
        # make sure the operation id isn't empty
        assert self.operation_id is not None
        # make sure the request id isn't empty
        assert self.request_id is not None
        # make sure attribute_groups is a list of Attributes
        assert len(self.attribute_groups) > 0
        for a in self.attribute_groups: assert isinstance(a, AttributeGroup)

        # convert the version, operation id, and request id to binary
        preattributes = struct.pack('>bbhi',
                                    self.version[0],
                                    self.version[1],
                                    self.operation_id,
                                    self.request_id)

        # convert the attribute groups to binary
        attribute_groups = ''.join([a.packed_value for a in self.attribute_groups])

        # conver the end-of-attributes-tag to binary
        end_of_attributes_tag = struct.pack('>b', AttributeTags.END)

        # convert the data to binary
        if self.data is not None:
            data = ''.join([struct.pack('>b', x) for x in self.data])
        else:
            data = ''

        # append everything together and return it
        return preattributes + attribute_groups + end_of_attributes_tag + data

    def __repr__(self):
        return '<IPPRequest (version=%r, operation_id=%x, request_id=%r, attribute_groups=%r)>' % (self.version, self.operation_id, self.request_id, self.attribute_groups)
