from .attribute import Attribute
import sys
import struct
import logging

# initialize logger
logger = logging.getLogger(__name__)

class AttributeGroup(object):
    """An AttributeGroup consists of an attribute-group-tag, followed
    by a sequence of Attributes. According to RFC 2565, 'Within an
    attribute-sequence, if two attributes have the same name, the
    first occurrence MUST be ignored.', so we can effectively treat
    this as an ordered dictionary.
    
    """

    def __init__(self, tag=None, attributes=[]):
        """Initialize an AttributeGroup.  An AttributeGroup can be
        initialized in three ways:

            AttributeGroup()
            AttributeGroup(tag)
            AttributeGroup(tag, attributes)

        Arguments:

            tag -- a signed char, holds the tag of the
                   attribute group

            attributes -- a list of attributes

        """

        if tag is not None:
            assert isinstance(tag, int), \
                   "tag must be a character!"

        self.tag = tag
        self.attributes = []
        self.extend(attributes)

    def __getitem__(self, name):
        """Returns a list of attributes which have name 'name'.
        
        """
        
        attribute = filter(lambda x: x.name == name, self.attributes)
        if attribute:
            return attribute[0]
        else:
            raise KeyError("Attribute %r not found" % name)

    def __contains__(self, name):
        return len(filter(lambda x: x.name == name, self.attributes))

    def __iter__(self):
        return (a.name for a in self.attributes)

    iterkeys = __iter__

    def __setitem__(self, name, attribute):
        """Sets an attribute in the attribute group. Note that the key
        is ignored and the attribute is queried for its name.
        
        """

        return self.append(attribute)

    def __delitem__(self, name):
        self.attributes = filter(lambda x: x.name != name,
				 self.attributes)

    def append(self, attribute):
        return self.extend([attribute])

    def extend(self, attributes):
        """Sets the attributes for the attribute group.
        
        """

        for a in attributes:
            assert isinstance(a, Attribute), \
                   "attribute must be of type Attribute!"

        for a in attributes:
            # XXX: Instead of replacing the attribute, do we want to
            # append the value to the attribute here?
            del self[a.name]
            self.attributes.append(a)

    @property
    def packed_value(self):
        """Convert the AttributeGroup to binary.
        
        """

        # convert the tag to binary
        tag = struct.pack('>b', self.tag)

        # convert each of the attributes to binary
        attributes = [a.packed_value for a in self.attributes]

        # concatenate everything and return
        return tag + ''.join(attributes)

    def __repr__(self):
        return '<IPPAttributeGroup (%r, %r)>' % (self.tag, self.attributes)
