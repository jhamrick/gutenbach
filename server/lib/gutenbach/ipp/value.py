from .constants import OutOfBandTags, IntegerTags, OctetStringTags, CharacterStringTags
import sys
import struct
import logging

# initialize logger
logger = logging.getLogger(__name__)

class Value(object):
    """An IPP value consists of a tag and a value.

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

    def __init__(self, tag=None, value=None):
        """Initialize a Value.  There are three different ways you can
        call this method:

            Value() -- creates an empty Value instance

            Value(tag, value) -- creates a Value instance from
            a non-binary value

        If you create an empty Value instance, once you have set
        tag and value, you can retrieve the packed value from
        the packed_value property.

        Arguments:

            tag -- one byte, identifying the type of value

            value -- variable size, containing the actual value.
            It should be a string or number.

        """

        # make sure the arguments are valid
        if value is not None:
            assert tag is not None, \
                   "tag must not be null because " + \
                   "value is not null!"

        # initialize member variables
        self.tag = tag # one byte, the type of value
        self.value     = value     # non-binary value of self.value

    @classmethod
    def unpack(cls, tag, packed_value):
        """Unpack a binary IPP value into a Value object.

        """
        return cls(tag, cls._unpack(tag, packed_value))

    @staticmethod
    def _unpack(tag, packed_value):
        """Given self.tag and self.packed_value, unpack the
        binary value into either a string or number.  These values
        MUST NOT be null.

        Returns: unpacked value

        """

        assert tag is not None, \
               "Cannot unpack values with unspecified value tag!"
        assert packed_value is not None, \
               "Cannot unpack null values!"

        value = None

        # out-of-band value tags
        if tag == OutOfBandTags.UNSUPPORTED or \
               tag == OutOfBandTags.DEFAULT or \
               tag == OutOfBandTags.UNKNOWN or \
               tag == OutOfBandTags.NO_VALUE:
            value_size = 0
            value = ''

        # integer value tags
        elif tag == IntegerTags.INTEGER:
            value = struct.unpack('>i', packed_value)[0]
        elif tag == IntegerTags.BOOLEAN:
            value = struct.unpack('>b', packed_value)[0]
        elif tag == IntegerTags.ENUM:
            value = struct.unpack('>i', packed_value)[0]

        
        elif tag == OctetStringTags.DATETIME:
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

            value = struct.unpack('>hbbbbbbcbb', packed_value)
            
        elif tag == OctetStringTags.RESOLUTION:
            # OCTET-STRING consisting of nine octets of 2
            # SIGNED-INTEGERs followed by a SIGNED-BYTE. The first
            # SIGNED-INTEGER contains the value of cross feed
            # direction resolution. The second SIGNED-INTEGER contains
            # the value of feed direction resolution. The SIGNED-BYTE
            # contains the units

            value = struct.unpack('>iib', packed_value)
            
        elif tag == OctetStringTags.RANGE_OF_INTEGER:
            # Eight octets consisting of 2 SIGNED-INTEGERs.  The first
            # SIGNED-INTEGER contains the lower bound and the second
            # SIGNED-INTEGER contains the upper bound.

            value = struct.unpack('>ii', packed_value)

        elif tag == OctetStringTags.TEXT_WITH_LANGUAGE or \
                 tag == OctetStringTags.NAME_WITH_LANGUAGE:
            a = struct.unpack('>h', packed_value[:2])[0]
            b = struct.unpack('>%ss' % a, packed_value[2:a+2])[0]
            c = struct.unpack('>h', packed_value[a+2:a+4])[0]
            d = struct.unpack('>%ss' % c, packed_value[a+4:][0])
            value = (a, b, c, d)

        # character string value tags
        elif tag == \
                 CharacterStringTags.TEXT_WITHOUT_LANGUAGE or \
                 tag == \
                 CharacterStringTags.NAME_WITHOUT_LANGUAGE:
            value = str(packed_value)
        elif tag == CharacterStringTags.GENERIC or \
                 tag == CharacterStringTags.KEYWORD or \
                 tag == CharacterStringTags.URI or \
                 tag == CharacterStringTags.URI_SCHEME or \
                 tag == CharacterStringTags.CHARSET or \
                 tag == CharacterStringTags.NATURAL_LANGUAGE or \
                 tag == CharacterStringTags.MIME_MEDIA_TYPE:
            value = str(packed_value)

        # anything else that we didn't handle
        else:
            if value is None:
                value = packed_value

        return value

    @property
    def packed_value(self):
        """Given self.tag and self.value, pack the value into
        binary form.  These values MUST NOT be null.

        Returns: packed_value

        """
        
        assert self.tag is not None, \
               "cannot pack value with null value tag!"
        assert self.value is not None, \
               "cannot pack null value!"

        packed_value = None

        # out-of-band value tags
        if self.tag == OutOfBandTags.UNSUPPORTED or \
               self.tag == OutOfBandTags.DEFAULT or \
               self.tag == OutOfBandTags.UNKNOWN or \
               self.tag == OutOfBandTags.NO_VALUE:
            packed_value = ''

        # integer value tags
        elif self.tag == IntegerTags.INTEGER:
            packed_value = struct.pack('>i', self.value)
        elif self.tag == IntegerTags.BOOLEAN:
            packed_value = struct.pack('>b', self.value)
        elif self.tag == IntegerTags.ENUM:
            packed_value = struct.pack('>i', self.value)

        # octet string value tags
        elif self.tag == OctetStringTags.DATETIME:
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

            packed_value = struct.pack('>hbbbbbbcbb', *self.value)
            
        elif self.tag == OctetStringTags.RESOLUTION:
            # OCTET-STRING consisting of nine octets of 2
            # SIGNED-INTEGERs followed by a SIGNED-BYTE. The first
            # SIGNED-INTEGER contains the value of cross feed
            # direction resolution. The second SIGNED-INTEGER contains
            # the value of feed direction resolution. The SIGNED-BYTE
            # contains the units

            packed_value = truct.pack('>iib', *self.value)
            
        elif self.tag == OctetStringTags.RANGE_OF_INTEGER:
            # Eight octets consisting of 2 SIGNED-INTEGERs.  The first
            # SIGNED-INTEGER contains the lower bound and the second
            # SIGNED-INTEGER contains the upper bound.

            packed_value = struct.pack('>ii', *self.value)

        elif self.tag == OctetStringTags.TEXT_WITH_LANGUAGE or \
                 self.tag == OctetStringTags.NAME_WITH_LANGUAGE:
            
            a_bin = struct.pack('>h', self.value[0])
            b_bin = struct.pack('>%ss' % self.value[0], self.value[1])
            c_bin = struct.pack('>h', self.value[2])
            d_bin = struct.pack('>%ss' % self.value[2], self.value[3])

            packed_value = a_bin + b_bin + c_bin + d_bin

        # character string value tags
        elif self.tag == \
                 CharacterStringTags.TEXT_WITHOUT_LANGUAGE or \
                 self.tag == \
                 CharacterStringTags.NAME_WITHOUT_LANGUAGE:

            packed_value = struct.pack('>%ss' % len(self.value),
                                       self.value)
                    
        elif self.tag == CharacterStringTags.GENERIC or \
                 self.tag == CharacterStringTags.KEYWORD or \
                 self.tag == CharacterStringTags.URI or \
                 self.tag == CharacterStringTags.URI_SCHEME or \
                 self.tag == CharacterStringTags.CHARSET or \
                 self.tag == CharacterStringTags.NATURAL_LANGUAGE or \
                 self.tag == CharacterStringTags.MIME_MEDIA_TYPE:
            
            packed_value = struct.pack('>%ss' % len(self.value),
                                       self.value)

        else:
            packed_value = self.value

        return packed_value

    @packed_value.setter
    def packed_value(self, packed_value):
        """Replace a value using a new packed value

        Unpacks a new packed_value (of the same tag).

        """
        self.value = self._unpack(self.tag, packed_value)

    @property
    def packed_value_size(self):
        """Get the size of the value in bytes.
        
        """
        
        return len(self.packed_value)

    @property
    def total_size(self):
        """Get the total size of the IPP value.
        
        """

        # 1 byte for the tag
        return self.packed_value_size + 1

    @property
    def pyobj(self):
        return (self.tag, self.value)

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return '<IPPValue (%x, %r)>' % (self.tag, self.value)
