__all__ = [
    'IPPException',
    'IPPClientException',
    'IPPServerException',

    'ClientErrorBadRequest',
    'ClientErrorForbidden',
    'ClientErrorNotAuthenticated',
    'ClientErrorNotAuthorized',
    'ClientErrorNotPossible',
    'ClientErrorTimeout',
    'ClientErrorNotFound',
    'ClientErrorGone',
    'ClientErrorRequestEntity',
    'ClientErrorRequestValue',
    'ClientErrorDocumentFormatNotSupported',
    'ClientErrorAttributes',
    'ClientErrorUriSchemeNotSupported',
    'ClientErrorCharsetNotSupported',
    'ClientErrorConflict',
    'ClientErrorCompressionNotSupported',
    'ClientErrorCompressionError',
    'ClientErrorDocumentFormatError',
    'ClientErrorDocumentAccessError',
    'ClientErrorAttributesNotSettable',
    'ClientErrorIgnoredAllSubscriptions',
    'ClientErrorTooManySubscriptions',
    'ClientErrorIgnoredAllNotifications',
    'ClientErrorPrintSupportFileNotFound',

    'ServerErrorInternalError',
    'ServerErrorOperationNotSupported',
    'ServerErrorServiceUnavailable',
    'ServerErrorVersionNotSupported',
    'ServerErrorDeviceError',
    'ServerErrorTemporaryError',
    'ServerErrorNotAccepting',
    'ServerErrorPrinterBusy',
    'ServerErrorJobCancelled',
    'ServerErrorMultipleJobsNotSupported',
    'ServerErrorPrinterIsDeactivated',
]
    

from .constants import ErrorCodes, AttributeTags
from .attributegroup import AttributeGroup

class IPPException(Exception):
    def __init__(self, message=""):
        self.message = message

    def __str__(self):
        return self.message

class IPPClientException(IPPException):
    def update_response(self, response):
        if hasattr(self, "ipp_error_code"):
            response.operation_id = self.ipp_error_code
        else:
            response.operation_id = ErrorCodes.BAD_REQUEST

class IPPServerException(IPPException):
    def update_response(self, response):
        if hasattr(self, "ipp_error_code"):
            response.operation_id = self.ipp_error_code
        else:
            response.operation_id = ErrorCodes.INTERNAL_ERROR
    
### Client error codes

class ClientErrorBadRequest(IPPClientException):
    ipp_error_code = ErrorCodes.BAD_REQUEST

class ClientErrorForbidden(IPPClientException):
    ipp_error_code = ErrorCodes.FORBIDDEN

class ClientErrorNotAuthenticated(IPPClientException):
    ipp_error_code = ErrorCodes.NOT_AUTHENTICATED

class ClientErrorNotAuthorized(IPPClientException):
    ipp_error_code = ErrorCodes.NOT_AUTHORIZED

class ClientErrorNotPossible(IPPClientException):
    ipp_error_code = ErrorCodes.NOT_POSSIBLE

class ClientErrorTimeout(IPPClientException):
    ipp_error_code = ErrorCodes.TIMEOUT

class ClientErrorNotFound(IPPClientException):
    ipp_error_code = ErrorCodes.NOT_FOUND

class ClientErrorGone(IPPClientException):
    ipp_error_code = ErrorCodes.GONE

class ClientErrorRequestEntity(IPPClientException):
    ipp_error_code = ErrorCodes.REQUEST_ENTITY

class ClientErrorRequestValue(IPPClientException):
    ipp_error_code = ErrorCodes.REQUEST_VALUE

class ClientErrorDocumentFormatNotSupported(IPPClientException):
    ipp_error_code = ErrorCodes.DOCUMENT_FORMAT

class ClientErrorAttributes(IPPClientException):
    ipp_error_code = ErrorCodes.ATTRIBUTES

    def __init__(self, message, attrs):
        self.message = message
        if hasattr(attrs, '__iter__'):
            self.bad_attrs = attrs
        else:
            self.bad_attrs = [attrs]

    def update_response(self, response):
        super(ClientErrorAttributes, self).update_response(response)
        response.attribute_groups.append(
            AttributeGroup(
                AttributeTags.UNSUPPORTED,
                self.bad_attrs))

class ClientErrorUriSchemeNotSupported(IPPClientException):
    ipp_error_code = ErrorCodes.URI_SCHEME

class ClientErrorCharsetNotSupported(IPPClientException):
    ipp_error_code = ErrorCodes.CHARSET

class ClientErrorConflict(IPPClientException):
    ipp_error_code = ErrorCodes.CONFLICT

class ClientErrorCompressionNotSupported(IPPClientException):
    ipp_error_code = ErrorCodes.COMPRESSION_NOT_SUPPORTED

class ClientErrorCompressionError(IPPClientException):
    ipp_error_code = ErrorCodes.COMPRESSION_ERROR

class ClientErrorDocumentFormatError(IPPClientException):
    ipp_error_code = ErrorCodes.DOCUMENT_FORMAT_ERROR

class ClientErrorDocumentAccessError(IPPClientException):
    ipp_error_code = ErrorCodes.DOCUMENT_ACCESS_ERROR

class ClientErrorAttributesNotSettable(IPPClientException):
    ipp_error_code = ErrorCodes.ATTRIBUTES_NOT_SETTABLE

class ClientErrorIgnoredAllSubscriptions(IPPClientException):
    ipp_error_code = ErrorCodes.IGNORED_ALL_SUBSCRIPTIONS

class ClientErrorTooManySubscriptions(IPPClientException):
    ipp_error_code = ErrorCodes.TOO_MANY_SUBSCRIPTIONS

class ClientErrorIgnoredAllNotifications(IPPClientException):
    ipp_error_code = ErrorCodes.IGNORED_ALL_NOTIFICATIONS

class ClientErrorPrintSupportFileNotFound(IPPClientException):
    ipp_error_code = ErrorCodes.PRINT_SUPPORT_FILE_NOT_FOUND

### Server error codes

class ServerErrorInternalError(IPPServerException):
    ipp_error_code = ErrorCodes.INTERNAL_ERROR

class ServerErrorOperationNotSupported(IPPServerException):
    ipp_error_code = ErrorCodes.OPERATION_NOT_SUPPORTED

class ServerErrorServiceUnavailable(IPPServerException):
    ipp_error_code = ErrorCodes.SERVICE_UNAVAILABLE

class ServerErrorVersionNotSupported(IPPServerException):
    ipp_error_code = ErrorCodes.VERSION_NOT_SUPPORTED

class ServerErrorDeviceError(IPPServerException):
    ipp_error_code = ErrorCodes.DEVICE_ERROR

class ServerErrorTemporaryError(IPPServerException):
    ipp_error_code = ErrorCodes.TEMPORARY_ERROR

class ServerErrorNotAccepting(IPPServerException):
    ipp_error_code = ErrorCodes.NOT_ACCEPTING

class ServerErrorPrinterBusy(IPPServerException):
    ipp_error_code = ErrorCodes.PRINTER_BUSY

class ServerErrorJobCancelled(IPPServerException):
    ipp_error_code = ErrorCodes.ERROR_JOB_CANCELLED

class ServerErrorMultipleJobsNotSupported(IPPServerException):
    ipp_error_code = ErrorCodes.MULTIPLE_JOBS_NOT_SUPPORTED

class ServerErrorPrinterIsDeactivated(IPPServerException):
    ipp_error_code = ErrorCodes.PRINTER_IS_DEACTIVATED
