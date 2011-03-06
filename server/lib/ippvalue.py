#!/usr/bin/python

import sys, struct, logging

# initialize logger
logger = logging.getLogger("ippLogger")

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

    def __init__(self, value_tag, value, unpack=True):
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

        if not unpack: return

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
