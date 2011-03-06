#!/usr/bin/python

import sys, struct, logging
from ippattribute import IPPAttribute

# initialize logger
logger = logging.getLogger("ippLogger")

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

    def getAttribute(self, name):
        return filter(lambda x: x.name == name, self.attributes)

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
