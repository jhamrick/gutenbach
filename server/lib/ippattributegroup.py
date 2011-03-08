#!/usr/bin/python

import sys, struct, logging
from ippattribute import Attribute

# initialize logger
logger = logging.getLogger("ippLogger")

class AttributeGroup():
    """
    An AttributeGroup consists of an attribute-group-tag, followed by
    a sequence of Attributes.
    """

    def __init__(self, attribute_group_tag=None, attributes=[]):
        """
        Initialize an AttributeGroup.  An AttributeGroup can be
        initialized in three ways:

            AttributeGroup()
            AttributeGroup(attribute_group_tag)
            AttributeGroup(attribute_group_tag, attributes)

        Arguments:

            attribute_group_tag -- a signed char, holds the tag of the
                                   attribute group

            attributes -- a list of attributes
        """

        if attribute_group_tag is not None:
            assert isinstance(attribute_group_tag, char), \
                   "attribute_group_tag must be a character!"
            

        if len(attributes) > 0:
            for a in attributes:
                assert isinstance(a, Attribute), \
                       "attribute must be of type Attribute!"

        self.attribute_group_tag = attribute_group_tag
        self.attributes = attributes

    def getAttribute(self, name):
        """
        Returns a list of attributes which have name 'name'.
        """
        
        return filter(lambda x: x.name == name, self.attributes)

    def getTag(self):
        """
        Return the attribute group tag.
        """

        return self.attribute_group_tag

    def getAttributes(self):
        """
        Return the list of attributes in this attribue group.
        """

        return self.attributes

    def setAttributes(self, attributes):
        """
        Sets the attributes for the attribute group.
        """

        for a in attributes:
            assert isinstance(a, Attribute), \
                   "attribute must be of type Attribute!"

        self.attributes = attributes

    def addAttribute(self, attribute):
        """
        Adds an attribute to the list of attributes for the attribute
        group.
        """
        
        assert isinstance(attribute, Attribute), \
               "attribute must be of type Attribute!"

        self.attributes.append(attribute)

    def setTag(self, tag):
        """
        Sets the attribute group tag.
        """

        assert isinstance(tag, char), \
               "attribute tag must be a character!"

        self.attribute_group_tag = tag

    def pack(self):
        """
        Convert the AttributeGroup to binary.
        """

        # conver the attribute_group_tag to binary
        tag = struct.pack('>b', self.attribute_group_tag)

        # convert each of the attributes to binary
        attributes = [a.toBinaryData() for a in self.attributes]

        # concatenate everything and return
        return tag + ''.join(attributes)
