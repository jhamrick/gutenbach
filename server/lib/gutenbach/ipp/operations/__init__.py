from ..attribute import Attribute
from ..attributegroup import AttributeGroup
from ..request import Request
from ..value import Value
from .. import errors
from .. import constants as consts

def verify_operations(request):
    """Pretty much all requests have the first attribute group for
    operation attributes, and these all have 'attributes-charset' and
    'attributes-natural-language' as the first two attributes.  This
    method just generically verifies that these attributes are there.

    """

    # XXX: check version
    if False:
        raise errors.VersionNotSupported(str(request.version))

    # XXX: check operation id
    if False:
        raise errors.OperationNotSupported(str(request.operation_id))

    # check operation attributes tag
    op_attrs = request.attribute_groups[0]
    if op_attrs.tag != consts.AttributeTags.OPERATION:
        raise errors.BadRequest(
            "Attribute group does not have OPERATION tag: 0x%x" % op_attrs.tag)

    # XXX: if these aren't valid, then you HAVE to return something
    # special.  See RFC 2911 3.1.6.1
    # # check compression
    # if False:
    #     raise errors.CompressionNotSupported

    # # check document format
    # if False:
    #     raise errors.DocumentFormatNotSupported

    # # check document uri
    # if False:
    #     raise errors.UriSchemeNotSupported

    # check charset
    charset_attr = op_attrs.attributes[0]
    if charset_attr.name != 'attributes-charset':
        raise errors.BadRequest(
            "Attribute is not attributes-charset: %s" % charset_attr.name)
    if len(charset_attr.values) != 1:
        raise errors.BadRequest(
            "Too many values for attributes-charset: %d" % len(charset_attr.values))
    # check charset value
    charset_value = charset_attr.values[0]
    if charset_value.tag != consts.operations_attribute_value_tags['attributes-charset']:
        raise errors.BadRequest(
            "Wrong tag for charset value: 0x%x" % charset_value.tag)
    if charset_value.value != 'utf-8':
        raise errors.CharsetNotSupported(str(charset_value.value))

    # check for attributes-natural-language
    natlang_attr = op_attrs.attributes[1]
    if natlang_attr.name != 'attributes-natural-language':
        raise errors.BadRequest(
            "Attribute is not attributes-natural-language: %s" % natlang_attr.name)
    if len(charset_attr.values) != 1:
        raise errors.BadRequest(
            "Too many values for attributes-natural-language: %s" % len(natlang_attr.values))
    # check natural language value
    natlang_value = natlang_attr.values[0]
    if natlang_value.tag != consts.operations_attribute_value_tags['attributes-natural-language']:
        raise errors.BadRequest(
            "Natural language value does not have NATURAL_LANGUAGE tag: 0x%x" % natlang_value.tag)
    if natlang_value.value != 'en-us':
        raise errors.Attributes(
            "Invalid natural language value: %s" % natlang_value.value, [natlang_attr])

    return dict([(attr.name, attr.values) for attr in op_attrs.attributes])

def verify_printer_uri(values):
    if len(values) != 1:
        raise errors.BadRequest(
            "Requesting printer uri attribute has too many values: %d" % len(values))
    uri_value = values[0]
    if uri_value.tag != consts.operations_attribute_value_tags['printer-uri']:
        raise errors.BadRequest(
            "Bad value tag (expected URI): 0x%x" % uri_value_tag)
    
    # actually get the printer name
    # XXX: hack -- CUPS will strip the port from the request, so
    # we can't do an exact comparison (also the hostname might be
    # different, depending on the CNAME or whether it's localhost)
    uri = uri_value.value.split("/")[-1]
    return uri

def verify_requesting_username(values):
    if len(values) != 1:
        raise errors.BadRequest(
            "Requesting user name attribute has too many values: %d" % len(values))
    requser_value = values[0]
    if requser_value.tag != consts.operations_attribute_value_tags['requesting-user-name']:
        raise errors.BadRequest(
            "Bad value tag (expected NAME_WITHOUT_LANGUAGE): 0x%x" % requser_value.tag)
    
    return requser_value.value

def make_empty_response(request):
    # Operation attributes -- typically the same for any request
    attributes = [
        Attribute(
            'attributes-charset',
            [Value(consts.operations_attribute_value_tags['attributes-charset'], 'utf-8')]),
        Attribute(
            'attributes-natural-language',
            [Value(consts.operations_attribute_value_tags['attributes-natural-language'],
                   'en-us')])
        ]
    # Put the operation attributes in a group
    attribute_group = AttributeGroup(
        consts.AttributeTags.OPERATION,
        attributes)

    # Set up the default response -- handlers will override these
    # values if they need to
    response_kwargs = {}
    response_kwargs['version']          = request.version
    response_kwargs['operation_id']     = consts.StatusCodes.OK
    response_kwargs['request_id']       = request.request_id
    response_kwargs['attribute_groups'] = [attribute_group]
    response = Request(**response_kwargs)

    return response

def make_job_attributes(attrs, request, response):
    ipp_attrs = []
    for attr, vals in attrs:
        ipp_vals = [Value(
            tag=consts.job_attribute_value_tags[attr],
            value=val) for val in vals]
        ipp_attrs.append(Attribute(name=attr, values=ipp_vals))
    response.attribute_groups.append(AttributeGroup(
        consts.AttributeTags.JOB, ipp_attrs))

def make_printer_attributes(attrs, request, response):
    ipp_attrs = []
    for attr, vals in attrs:
        ipp_vals = [Value(
            tag=consts.printer_attribute_value_tags[attr],
            value=val) for val in vals]
        ipp_attrs.append(Attribute(name=attr, values=ipp_vals))
    response.attribute_groups.append(AttributeGroup(
        consts.AttributeTags.PRINTER, ipp_attrs))


from cups_get_classes import verify_cups_get_classes_request, make_cups_get_classes_response
from cups_get_default import verify_cups_get_default_request, make_cups_get_default_response
from cups_get_printers import verify_cups_get_printers_request, make_cups_get_printers_response

from get_jobs import verify_get_jobs_request, make_get_jobs_response
from get_printer_attributes import verify_get_printer_attributes_request
from get_printer_attributes import make_get_printer_attributes_response

__all__ = ['verify_cups_get_classes_request',
           'make_cups_get_classes_response',
           'verify_cups_get_default_request',
           'make_cups_get_default_response',
           'verify_cups_get_printers_request',
           'make_cups_get_printers_response',
           'verify_get_jobs_request',
           'make_get_jobs_response',
           'verify_get_printer_attributes_request',
           'make_get_printer_attributes_response',

           'verify_operations',
           'verify_printer_uri',
           'verify_requesting_username',

           'make_empty_response',
           'make_job_attributes',
           'make_printer_attributes']
