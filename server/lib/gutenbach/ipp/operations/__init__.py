from ..attribute import Attribute
from ..attributegroup import AttributeGroup
from ..request import Request
from ..value import Value
from .. import errors
from .. import constants as consts
from .. import object_attributes

def verify_operations(request):
    """Pretty much all requests have the first attribute group for
    operation attributes, and these all have 'attributes-charset' and
    'attributes-natural-language' as the first two attributes.  This
    method just generically verifies that these attributes are there.

    """

    # XXX: check version
    if False:
        raise errors.ClientErrorVersionNotSupported(str(request.version))

    # XXX: check operation id
    if False:
        raise errors.ClientErrorOperationNotSupported(str(request.operation_id))

    # check operation attributes tag
    op_attrs = request.attribute_groups[0]
    if op_attrs.tag != consts.AttributeTags.OPERATION:
        raise errors.ClientErrorBadRequest(
            "Attribute group does not have OPERATION tag: 0x%x" % op_attrs.tag)

    # XXX: if these aren't valid, then you HAVE to return something
    # special.  See RFC 2911 3.1.6.1
    # # check compression
    # if False:
    #     raise errors.ClientErrorCompressionNotSupported

    # # check document format
    # if False:
    #     raise errors.ClientErrorDocumentFormatNotSupported

    # # check document uri
    # if False:
    #     raise errors.ClientErrorUriSchemeNotSupported

    # check charset
    charset_attr = op_attrs.attributes[0]
    expected = object_attributes.AttributesCharset('utf-8')
    if charset_attr != expected:
        raise errors.ClientErrorBadRequest("%s != %s" % (charset_attr, expected))

    # check for attributes-natural-language
    natlang_attr = op_attrs.attributes[1]
    expected = object_attributes.AttributesNaturalLanguage('en-us')
    if natlang_attr != expected:
        raise errors.ClientErrorBadRequest("%s != %s" % (natlang_attr, expected))

    return dict([(attr.name, attr) for attr in op_attrs.attributes])

def verify_printer_uri(uri_attr):
    expected = object_attributes.PrinterUri(uri_attr.values[0].value)
    if uri_attr != expected:
        raise errors.ClientErrorBadRequest("%s != %s" % (uri_attr, expected))
    
    # actually get the printer name
    # XXX: hack -- CUPS will strip the port from the request, so
    # we can't do an exact comparison (also the hostname might be
    # different, depending on the CNAME or whether it's localhost)
    uri = uri_attr.values[0].value.split("/")[-1]
    return uri

def verify_requesting_username(username_attr):
    expected = object_attributes.RequestingUserName(username_attr.values[0].value)
    if username_attr != expected:
        raise errors.ClientErrorBadRequest("%s != %s" % (username_attr, expected))
    return username_attr.values[0].value

def make_empty_response(request):
    # Operation attributes -- typically the same for any request
    attributes = AttributeGroup(
        consts.AttributeTags.OPERATION,
        [object_attributes.AttributesCharset('utf-8'),
         object_attributes.AttributesNaturalLanguage('en-us')])

    # Set up the default response -- handlers will override these
    # values if they need to
    response_kwargs = {}
    response_kwargs['version']          = request.version
    response_kwargs['operation_id']     = consts.StatusCodes.OK
    response_kwargs['request_id']       = request.request_id
    response_kwargs['attribute_groups'] = [attributes]
    response = Request(**response_kwargs)

    return response

def make_job_attributes(attrs, request, response):
    response.attribute_groups.append(AttributeGroup(
        consts.AttributeTags.JOB, attrs))

def make_printer_attributes(attrs, request, response):
    response.attribute_groups.append(AttributeGroup(
        consts.AttributeTags.PRINTER, attrs))

from cups_get_classes import verify_cups_get_classes_request, make_cups_get_classes_response
from cups_get_default import verify_cups_get_default_request, make_cups_get_default_response
from cups_get_document import verify_cups_get_document_request, make_cups_get_document_response
from cups_get_printers import verify_cups_get_printers_request, make_cups_get_printers_response

from cancel_job import verify_cancel_job_request, make_cancel_job_response
from create_job import verify_create_job_request, make_create_job_response
from get_jobs import verify_get_jobs_request, make_get_jobs_response
from get_printer_attributes import make_get_printer_attributes_response
from get_printer_attributes import verify_get_printer_attributes_request
from pause_printer import verify_pause_printer_request, make_pause_printer_response
from print_job import verify_print_job_request, make_print_job_response
from print_uri import verify_print_uri_request, make_print_uri_response
from promote_job import verify_promote_job_request, make_promote_job_response
from restart_job import verify_restart_job_request, make_restart_job_response
from resume_printer import verify_resume_printer_request, make_resume_printer_response
from send_document import verify_send_document_request, make_send_document_response
from send_uri import verify_send_uri_request, make_send_uri_response
from set_job_attributes import make_set_job_attributes_response
from set_job_attributes import verify_set_job_attributes_request
from set_printer_attributes import make_set_printer_attributes_response
from set_printer_attributes import verify_set_printer_attributes_request
from validate_job import verify_validate_job_request, make_validate_job_response

__all__ = ['verify_cups_get_classes_request', 'make_cups_get_classes_response'
           'verify_cups_get_default_request', 'make_cups_get_default_response'
           'verify_cups_get_document_request', 'make_cups_get_document_response'
           'verify_cups_get_printers_request', 'make_cups_get_printers_response'

           'verify_cancel_job_request', 'make_cancel_job_response'
           'verify_create_job_request', 'make_create_job_response'
           'verify_get_jobs_request', 'make_get_jobs_response'
           'make_get_printer_attributes_response'
           'verify_get_printer_attributes_request'
           'verify_pause_printer_request', 'make_pause_printer_response'
           'verify_print_job_request', 'make_print_job_response'
           'verify_print_uri_request', 'make_print_uri_response'
           'verify_promote_job_request', 'make_promote_job_response'
           'verify_restart_job_request', 'make_restart_job_response'
           'verify_resume_printer_request', 'make_resume_printer_response'
           'verify_send_document_request', 'make_send_document_response'
           'verify_send_uri_request', 'make_send_uri_response'
           'make_set_job_attributes_response'
           'verify_set_job_attributes_request'
           'make_set_printer_attributes_response'
           'verify_set_printer_attributes_request'
           'verify_validate_job_request', 'make_validate_job_response'

           'verify_operations',
           'verify_printer_uri',
           'verify_requesting_username',

           'make_empty_response',
           'make_job_attributes',
           'make_printer_attributes']
