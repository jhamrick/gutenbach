#!/usr/bin/python

import sys, struct, logging
from ippconstants import *

# initialize logger
logger = logging.getLogger("ippLogger")

class Value():
    """
    An IPP value consists of a tag and a value.

    From RFC 2565:
     -----------------------------------------------
     |                   value-tag                 |   1 byte
     -----------------------------------------------
     |            name-length  (value is 0x0000)   |   2 bytes
     -----------------------------------------------
     |              value-length  (value is v)     |   2 bytes
     -----------------------------------------------
     |                     value                   |   v bytes
     -----------------------------------------------    
    """

    def __init__(self, value_tag=None, value=None, unpack=True):
        """
        Initialize a Value.  There are three different ways you can
        call this method:

            Value() -- creates an empty Value instance

            Value(value_tag, value) -- creates a Value instance from
            binary values

            Value(value_tag, value, unpack=False) -- creates a Value
            instance from non-binary values

        If you create an empty Value instance, once you have set
        value_tag and value, you should call pack(), or if you set
        value_tag and binary_value, call unpack().

        Arguments:

            value_tag -- one byte, identifying the type of value

            value -- variable size, containing the actual value.  If
            unpack is True, then this should be a binary value,
            otherwise it should be a string or number.

            unpack -- boolean which indicates whether the value passed
            in is binary (i.e., should be unpacked) or not (i.e., does
            not need to be unpacked)
        """

        # make sure the arguments are valid
        if value_tag is not None:
            assert value is not None, \
                   "value must not be null because " + \
                   "value_tag is not null!"
        elif value_tag is None:
            assert value is None, \
                   "value must be null because value_tag is null!"

        # initialize member variables
        self.value_tag    = None # one byte, the type of value
        self.value        = None # non-binary value of self.value
        self.value_size   = None # size of self.value
        self.binary_value = None # binary value of self.value

        if value_tag is not None and value is not None:
            if unpack:
                self.value_tag = value_tag
                self.binary_value = value
                self.unpack()
                self.pack()
            else:
                self.value_tag = value_tag
                self.value = value
                self.pack()
                self.unpack()

    def unpack(self):
        """
        Given self.value_tag and self.binary_value, unpack the binary
        value into either a string or number.  These values MUST NOT
        be null.  Furthermore, if self.value and self.value_size are
        set, this method will check to make sure that unpacking
        self.binary_value matches up.

        Returns: tuple of (value_size, value)
        """

        assert self.value_tag is not None, \
               "Cannot unpack values with unspecified value tag!"
        assert self.binary_value is not None, \
               "Cannot unpack null values!"

        value_size = None
        value = None

        # out-of-band value tags
        if self.value_tag == OutOfBandTags.UNSUPPORTED or \
               self.value_tag == OutOfBandTags.DEFAULT or \
               self.value_tag == OutOfBandTags.UNKNOWN or \
               self.value_tag == OutOfBandTags.NO_VALUE:
            value_size = 0
            value = ''

        # integer value tags
        elif self.value_tag == IntegerTags.INTEGER:
            value_size = 4
            value = struct.unpack('>i', self.binary_value)[0]
        elif self.value_tag == IntegerTags.BOOLEAN:
            value_size = 1
            value = struct.unpack('>?', self.binary_value)[0]
        elif self.value_tag == IntegerTags.ENUM:
            value_size = 4
            value = struct.unpack('>i', self.binary_value)[0]

        
        elif self.value_tag == OctetStringTags.DATETIME:
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

            value_size = 11
            value = struct.unpack('>hbbbbbbcbb', self.binary_value)[0]
            
        elif self.value_tag == OctetStringTags.RESOLUTION:
            # OCTET-STRING consisting of nine octets of 2
            # SIGNED-INTEGERs followed by a SIGNED-BYTE. The first
            # SIGNED-INTEGER contains the value of cross feed
            # direction resolution. The second SIGNED-INTEGER contains
            # the value of feed direction resolution. The SIGNED-BYTE
            # contains the units

            value_size = 9
            value = struct.unpack('>iib', self.binary_value)
            
        elif self.value_tag == OctetStringTags.RANGE_OF_INTEGER:
            # Eight octets consisting of 2 SIGNED-INTEGERs.  The first
            # SIGNED-INTEGER contains the lower bound and the second
            # SIGNED-INTEGER contains the upper bound.

            value_size = 8
            value = struct.unpack('>ii', self.binary_value)

        elif self.value_tag == OctetStringTags.TEXT_WITH_LANGUAGE or \
                 self.value_tag == OctetStringTags.NAME_WITH_LANGUAGE:
            a = struct.unpack('>h', self.binary_value[:2])[0]
            b = struct.unpack('>%ss' % a, self.binary_value[2:a+2])[0]
            c = struct.unpack('>h', self.binary_value[a+2:a+4])[0]
            d = struct.unpack('>%ss' % c, self.binary_value[a+4:][0])
            value_size = 4 + a + c
            value = (a, b, c, d)

        # character string value tags
        elif self.value_tag == \
                 CharacterStringTags.TEXT_WITHOUT_LANGUAGE or \
                 self.value_tag == \
                 CharacterStringTags.NAME_WITHOUT_LANGUAGE:
            value_size = len(str(self.binary_value))
            value = str(self.binary_value)
        elif self.value_tag == CharacterStringTags.GENERIC or \
                 self.value_tag == CharacterStringTags.KEYWORD or \
                 self.value_tag == CharacterStringTags.URI or \
                 self.value_tag == CharacterStringTags.URI_SCHEME or \
                 self.value_tag == CharacterStringTags.CHARSET or \
                 self.value_tag == CharacterStringTags.NATURAL_LANGUAGE or \
                 self.value_tag == CharacterStringTags.MIME_MEDIA_TYPE:
            value_size = len(str(self.binary_value))
            value = str(self.binary_value)

        # anything else that we didn't handle
        else:
            if value_size is None and value is None:
                value_size = len(self.binary_value)
                value = self.binary_value

        if self.value_size is not None:
            assert value_size == self.value_size, \
                   "unpacked value_size is not the same " + \
                   "as self.value_size!"
        if self.value is not None:
            assert value == self.value, \
                   "unpacked value is not the same as self.value!"

        self.value_size = value_size
        self.value = value
        
        return value_size, value

    def pack(self):
        """
        Given self.value_tag and self.value, pack the value into
        binary formo.  These values MUST NOT be null.  Furthermore, if
        self.binary_value and self.value_size are set, this method
        will check to make sure that packing self.value matches up.

        Returns: tuple of (value_size, binary_value)
        """
        
        assert self.value_tag is not None, \
               "cannot pack value with null value tag!"
        assert self.value is not None, \
               "cannot pack null value!"

        value_size = None
        binary_value = None

        # out-of-band value tags
        if self.value_tag == OutOfBandTags.UNSUPPORTED or \
               self.value_tag == OutOfBandTags.DEFAULT or \
               self.value_tag == OutOfBandTags.UNKNOWN or \
               self.value_tag == OutOfBandTags.NO_VALUE:
            value_size = 0
            binary_value = ''

        # integer value tags
        elif self.value_tag == IntegerTags.INTEGER:
            value_size = 4
            binary_value = struct.pack('>i', self.value)
        elif self.value_tag == IntegerTags.BOOLEAN:
            value_size = 1
            binary_value = struct.pack('>?', self.value)
        elif self.value_tag == IntegerTags.ENUM:
            value_size = 4
            binary_value = struct.pack('>i', self.value)

        # octet string value tags
        elif self.value_tag == OctetStringTags.DATETIME:
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

            value_size = 11
            binary_value = struct.pack('>hbbbbbbcbb', self.value)
            
        elif self.value_tag == OctetStringTags.RESOLUTION:
            # OCTET-STRING consisting of nine octets of 2
            # SIGNED-INTEGERs followed by a SIGNED-BYTE. The first
            # SIGNED-INTEGER contains the value of cross feed
            # direction resolution. The second SIGNED-INTEGER contains
            # the value of feed direction resolution. The SIGNED-BYTE
            # contains the units

            value_size = 9
            binary_value = truct.pack('>iib', self.value)
            
        elif self.value_tag == OctetStringTags.RANGE_OF_INTEGER:
            # Eight octets consisting of 2 SIGNED-INTEGERs.  The first
            # SIGNED-INTEGER contains the lower bound and the second
            # SIGNED-INTEGER contains the upper bound.

            value_size = 8
            binary_value = struct.pack('>ii', self.value)

        elif self.value_tag == OctetStringTags.TEXT_WITH_LANGUAGE or \
                 self.value_tag == OctetStringTags.NAME_WITH_LANGUAGE:
            
            a_bin = struct.pack('>h', self.value[0])
            b_bin = struct.pack('>%ss' % self.value[0], self.value[1])
            c_bin = struct.pack('>h', self.value[2])
            d_bin = struct.pack('>%ss' % self.value[2], self.value[3])

            value_size = 4 + self.value[0] + self.value[2]
            binary_value = a_bin + b_bin + c_bin + d_bin

        # character string value tags
        elif self.value_tag == \
                 CharacterStringTags.TEXT_WITHOUT_LANGUAGE or \
                 self.value_tag == \
                 CharacterStringTags.NAME_WITHOUT_LANGUAGE:

            value_size = len(self.value)
            binary_value = struct.pack('>%ss' % len(self.value),
                                       self.value)
                    
        elif self.value_tag == CharacterStringTags.GENERIC or \
                 self.value_tag == CharacterStringTags.KEYWORD or \
                 self.value_tag == CharacterStringTags.URI or \
                 self.value_tag == CharacterStringTags.URI_SCHEME or \
                 self.value_tag == CharacterStringTags.CHARSET or \
                 self.value_tag == CharacterStringTags.NATURAL_LANGUAGE or \
                 self.value_tag == CharacterStringTags.MIME_MEDIA_TYPE:
            
            value_size = len(self.value)
            binary_value = struct.pack('>%ss' % len(self.value),
                                       self.value)

        else:
            value_size = len(self.value)
            binary_value = self.value

        if self.value_size is not None:
            assert value_size == self.value_size, \
                   "packed value size is not the same as " + \
                   "self.value_size!"
        if self.binary_value is not None:
            assert binary_value == self.binary_value, \
                   "packed binary value is not the same as " + \
                   "self.binary_value!"

        self.value_size = value_size
        self.binary_value = binary_value

        return value_size, binary_value

    def verify(self):
        """
        Verifies that the binary and non-binary values for this Value
        instance line up.  All of self.value, self.binary_value,
        self.value_size, and self.value_tag must be defined.

        This function will throw an assertion error if the Value
        instance is not valid.
        """

        assert self.value is not None, \
               "value is null!"
        assert self.binary_value is not None, \
               "binary value is null!"
        assert self.value_size is not None, \
               "value size is unknown!"
        assert self.value_tag is not None, \
               "value type is unknown!"

        self.pack()
        self.unpack()

    def getValue(self):
        """
        Get the non-binary value.
        """

        return self.value

    def getBinaryValue(self):
        """
        Get the binary value.
        """
        
        return self.binary_value

    def getValueTag(self):
        """
        Get the value tag (type of value). This is an integer
        corresponding to a value in ippconstants.
        """
        
        return self.value_tag

    def getSize(self):
        """
        Get the size of the value in bytes.
        """
        
        return self.value_size

    def setValue(self, value):
        """
        Set the non-binary value.
        """
        
        self.value = value

    def setBinaryValue(self, binary_value):
        """
        Set the binary value.
        """
        self.binary_value = binary_value

    def setValueTag(self, value_tag):
        """
        Set the type (tag) of the value.  This should correspond to an
        integer defined in ippconstants.
        """
        
        self.value_tag = value_tag

    def setSize(self, size):
        """
        Set the size of the value in bytes.
        """
        
        self.value_size = size

    def __str__(self):
        return self.value
