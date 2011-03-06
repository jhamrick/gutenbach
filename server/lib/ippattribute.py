#!/usr/bin/python

import sys, struct, logging
from ippvalue import Value

# initialize logger
logger = logging.getLogger("ippLogger")

class Attribute():
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
        Initialize an Attribute.
        
        Arguments:

            name -- the name of the attribute

            values -- a list of Values.  May not be empty.
        """

        # make sure name isn't empty
        assert name is not None
         
        # make sure the list of values isn't empty
        assert len(values) > 0
        # make sure each value is a Value
        for value in values: assert isinstance(value, Value)
         
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
