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

    def __init__(self, name=None, values=[]):
        """
        Initialize an Attribute.  This function can be called in three
        different ways:

            Attribute() -- creates an empty Attribute

            Attribute(name) -- creates an empty Attribute with a name

            Attribute(name, values) -- creates an Attribute
            initialized with a name and list of values
        
        Arguments:

            name -- the name of the attribute

            values -- a list of Values.  May not be empty.
        """

        if name is not None:
            assert isinstance(name, str), \
                   "Attribute name must be a string!"
        for value in values:
            assert isinstance(value, Value), \
                   "Value must be of type Value"

        self.name = None
        self.values = None

        if name is not None:
            self.name = name
        if name is not None and len(values) > 0:
            self.values = values
            self.binary = self.pack()
            self.verify()

    def pack(self):
        """
        Packs the attribute data into binary data.
        """

        assert self.name is not None, \
               "cannot pack unnamed attribute!"
        assert len(self.values) > 0, \
               "cannot pack empty attribute!"

        # get the binary data for all the values
        values = []
        length = 0
        for v, i in zip(self.values, xrange(len(self.values))):

            # get the name length (0 for everything but the first
            # value)
            if i == 0:
                name_length = len(self.name)
            else:
                name_length = 0

            # get the value length and binary value
            value_length, value_bin = v.pack()

            logger.debug("dumping name_length : %i" % name_length)
            logger.debug("dumping name : %s" % self.name)
            logger.debug("dumping value_length : %i" % value_length)
            logger.debug("dumping value : %s" % v.getValue())

            # the value tag in binary
            value_tag_bin = struct.pack('>b', v.getValueTag())

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

            length += 2            # name-length
            length += name_length  # name
            length += value_length # value
                
        # concatenate everything together and return it along with the
        # total length of the attribute
        return length, ''.join(values)

    def getName(self):
        """
        Get the attribute's name.
        """
        
        return self.name

    def getValues(self):
        """
        Get the list of values contained in the attribute.
        """
        
        return self.values

    def setName(self, name):
        """
        Set the attribute's name.
        """

        assert isinstance(name, str), \
               "name must be a string!"
        
        self.name = name

    def setValues(self, values):
        """
        Set the list of values contained in the attribute.
        """

        for v in values:
            assert isinstance(v, Value), \
                   "value must be of type Value!"
        
        self.values = values

    def addValue(self, value):
        """
        Add a new value to the list of values contained in the
        attribute."

        assert isinstance(value, Value), \
               "value must be of type Value!"

        self.values.append(value)

    def getSize(self):
        """
        Gets the total size of the attribute.
        """

        size = 2 + len(self.name)
        for v in self.values:
            size += v.getTotalSize()

    def verify(self):
        """
        Check to make sure that the Attribute is valid.  This means
        that is should have a name and a list of values, and that its
        binary representation should match up to the stored binary
        representation.
        """
        
        assert self.name is not None, \
               "attribute has no name!"
        assert len(self.value) > 0, \
               "attribute has no values!"

        size, bindata = self.pack()

        assert size == self.getSize(), \
               "pack size does not match self.getSize()!"
        assert bindata == self.binary_data, \
               "packed binary data does not match self.binary_data!"

    def __str__(self):
        if len(self.values) > 0:
            values = [str(v) for v in self.values]
        else:
            values = "None"

        if self.name is None:
            name = "None"
        else:
            name = self.name
        
        return "%s: %s" % (name, str(values))
