from .value import Value
from .attribute import Attribute
from .attributegroup import AttributeGroup
from .request import Request
from .constants import AttributeTags, Tags
import exceptions as err

from collections import OrderedDictionary as odict

def verify_operations(request):
    """Pretty much all requests have the first attribute group for
    operation attributes, and these all have 'attributes-charset' and
    'attributes-natural-language' as the first two attributes.  This
    method just generically verifies that these attributes are there.

    """

    # check operation attributes tag
    op_attrs = request.attribute_groups[0]
    if op_attrs.tag != AttributeTags.OPERATION:
        raise err.BadRequest(
            "Attribute group does not have OPERATION tag: 0x%x" % op_attrs.tag)

    # check charset attribute
    charset_attr = op_attrs.attributes[0]
    if charset_attr.name != 'attributes-charset':
        raise err.BadRequest(
            "Attribute is not attributes-charset: %s" % charset_attr.name)
    if len(charset_attr.values) != 1:
        raise err.BadRequest(
            "Too many values for attributes-charset: %d" % len(charset_attr.values))

    # check charset value
    charset_value = charset_attr.values[0]
    if charset_value.tag != Tags.CHARSET:
        raise err.BadRequest(
            "Charset value does not have CHARSET tag: 0x%x" % charset_value.tag)
    if charset_value.value != 'utf-8':
        raise err.Charset(
            "Invalid charset value: %s" % charset_value.value)

    # check for attributes-natural-language
    natlang_attr = op_attrs.attributes[1]
    if natlang_attr.name != 'attributes-natural-language':
        raise err.BadRequest(
            "Attribute is not attributes-natural-language: %s" % natlang_attr.name)
    if len(charset_attr.values) != 1:
        raise err.BadRequest(
            "Too many values for attributes-natural-language: %s" % len(natlang_attr.values))

    # check natural language value
    natlang_value = natlang_attr.values[0]
    if natlang_value.tag != Tags.NATURAL_LANGUAGE:
        raise err.BadRequest(
            "Natural language value does not have NATURAL_LANGUAGE tag: 0x%x" natlang_value.tag)
    if natlang_value.value != 'en-us':
        raise err.Attributes(
            "Invalid natural language value: %s" % natlang_value.value, [natlang_attr])

def verify_requesting_username(requser_attr):
    if requser_attr.tag != Tags.NAME_WITHOUT_LANGUAGE:
        raise err.BadRequest(
            "Requesting user name attribute tag is not NAME_WITHOUT_LANGUAGE: 0x%x" % \
            requser_attr.tag)
    if len(requser_attr.values) != 1:
        raise err.BadRequest(
            "Requesting user name attribute has too many values: %d" % len(requser_attr.values))
    requser_value = requser_attr.values[0]
    if requser_value.tag != Tags.NAME_WITHOUT_LANGUAGE:
        raise err.BadRequest(
            "Requesting user name value tag is not NAME_WITHOUT_LANGUAGE: 0x%x" % \
            requser_value.tag)
    return requser_value.value

def verify_get_jobs_request(request):
    """RFC 2911 3.2.6.1 Get-Jobs Request

    The client submits the Get-Jobs request to a Printer object.
    
    The following groups of attributes are part of the Get-Jobs
    Request:

    Group 1: Operation Attributes
        Natural Language and Character Set:
            The 'attributes-charset' and
            'attributes-natural-language' attributes as described
            in section 3.1.4.1.
        Target:
            The 'printer-uri' (uri) operation attribute which is
            the target for this operation as described in section
            3.1.5.
        Requesting User Name:
            The 'requesting-user-name' (name(MAX)) attribute
            SHOULD be supplied by the client as described in
            section 8.3.
        'limit' (integer(1:MAX)):
            The client OPTIONALLY supplies this attribute. The
            Printer object MUST support this attribute. It is an
            integer value that determines the maximum number of
            jobs that a client will receive from the Printer even
            if 'which-jobs' or 'my-jobs' constrain which jobs are
            returned. The limit is a 'stateless limit' in that if
            the value supplied by the client is ’N’, then only the
            first ’N’ jobs are returned in the Get-Jobs Response.
            There is no mechanism to allow for the next ’M’ jobs
            after the first ’N’ jobs. If the client does not
            supply this attribute, the Printer object responds
            with all applicable jobs.
        'requested-attributes' (1setOf type2 keyword):
            The client OPTIONALLY supplies this attribute. The
            Printer object MUST support this attribute. It is a
            set of Job attribute names and/or attribute groups
            names in whose values the requester is
            interested. This set of attributes is returned for
            each Job object that is returned. The allowed
            attribute group names are the same as those defined in
            the Get-Job-Attributes operation in section 3.3.4. If
            the client does not supply this attribute, the Printer
            MUST respond as if the client had supplied this
            attribute with two values: ’job-uri’ and ’job-id’.
        'which-jobs' (type2 keyword):
            The client OPTIONALLY supplies this attribute. The
            Printer object MUST support this attribute. It
            indicates which Job objects MUST be returned by the
            Printer object. The values for this attribute are:
             - ’completed’: This includes any Job object whose
               state is ’completed’, ’canceled’, or ’aborted’.
             - ’not-completed’: This includes any Job object whose
               state is ’pending’, ’processing’,
               ’processing-stopped’, or ’pending-held’.
            A Printer object MUST support both values. However, if
            the implementation does not keep jobs in the
            ’completed’, ’canceled’, and ’aborted’ states, then it
            returns no jobs when the ’completed’ value is
            supplied.  If a client supplies some other value, the
            Printer object MUST copy the attribute and the
            unsupported value to the Unsupported Attributes
            response group, reject the request, and return the
            ’client-error-attributes-or-values-not-supported’
            status code.  If the client does not supply this
            attribute, the Printer object MUST respond as if the
            client had supplied the attribute with a value of
            ’not-completed’.
        'my-jobs' (boolean):
            The client OPTIONALLY supplies this attribute. The
            Printer object MUST support this attribute. It
            indicates whether jobs from all users or just the jobs
            submitted by the requesting user of this request MUST
            be considered as candidate jobs to be returned by the
            Printer object. If the client does not supply this
            attribute, the Printer object MUST respond as if the
            client had supplied the attribute with a value of
            ’false’, i.e., jobs from all users. The means for
            authenticating the requesting user and matching the
            jobs is described in section 8.

    """

    # generic operations verification
    verify_operations(request)

    # requesting username
    requser = verify_requesting_username(request.attributes[2])
    out = {'requesting-user-name': requser}

    # make the rest of the attributes into a dictionary
    attrs = dict([(attr.name, attr.values) for attr in request.attributes[3:]])
    
    if 'limit' in attrs:
        out['limit'] = None # XXX

    if 'requested-attributes' in attrs:
        out['requested-attributes'] = None # XXX

    if 'which-jobs' in attrs:
        out['which-jobs'] = None # XXX

    if 'my-jobs' in attrs:
        out['my-jobs'] = None # XXX

    return out
