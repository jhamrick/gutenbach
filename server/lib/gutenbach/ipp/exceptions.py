from .constants import ErrorCodes

class IPPException(Exception):
    def __init__(self, message):
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

class BadRequest(IPPClientException):
    ipp_error_code = ErrorCodes.BAD_REQUEST)

class Forbidden(IPPClientException):
    ipp_error_code = ErrorCodes.FORBIDDEN)

class NotAuthenticated(IPPClientException):
    ipp_error_code = ErrorCodes.NOT_AUTHENTICATED)

class NotAuthorized(IPPClientException):
    ipp_error_code = ErrorCodes.NOT_AUTHORIZED)

class NotPossible(IPPClientException):
    ipp_error_code = ErrorCodes.NOT_POSSIBLE)

class Timeout(IPPClientException):
    ipp_error_code = ErrorCodes.TIMEOUT)

class NotFound(IPPClientException):
    ipp_error_code = ErrorCodes.NOT_FOUND)

class Gone(IPPClientException):
    ipp_error_code = ErrorCodes.GONE)

class RequestEntity(IPPClientException):
    ipp_error_code = ErrorCodes.REQUEST_ENTITY)

class RequestValue(IPPClientException):
    ipp_error_code = ErrorCodes.REQUEST_VALUE)

class DocumentFormatNotSupported(IPPClientException):
    ipp_error_code = ErrorCodes.DOCUMENT_FORMAT)

class Attributes(IPPClientException):
    ipp_error_code = ErrorCodes.ATTRIBUTES)

    def __init__(self, message, attrs):
        self.message = message
        self.bad_attrs = attrs

    def update_response(self, response):
        pass

class UriSchemeNotSupported(IPPClientException):
    ipp_error_code = ErrorCodes.URI_SCHEME)

class CharsetNotSupported(IPPClientException):
    ipp_error_code = ErrorCodes.CHARSET)

class Conflict(IPPClientException):
    ipp_error_code = ErrorCodes.CONFLICT)

class CompressionNotSupported(IPPClientException):
    ipp_error_code = ErrorCodes.COMPRESSION_NOT_SUPPORTED)

class CompressionError(IPPClientException):
    ipp_error_code = ErrorCodes.COMPRESSION_ERROR)

class DocumentFormatError(IPPClientException):
    ipp_error_code = ErrorCodes.DOCUMENT_FORMAT_ERROR)

class DocumentAccessError(IPPClientException):
    ipp_error_code = ErrorCodes.DOCUMENT_ACCESS_ERROR)

class AttributesNotSettable(IPPClientException):
    ipp_error_code = ErrorCodes.ATTRIBUTES_NOT_SETTABLE)

class IgnoredAllSubscriptions(IPPClientException):
    ipp_error_code = ErrorCodes.IGNORED_ALL_SUBSCRIPTIONS)

class TooManySubscriptions(IPPClientException):
    ipp_error_code = ErrorCodes.TOO_MANY_SUBSCRIPTIONS)

class IgnoredAllNotifications(IPPClientException):
    ipp_error_code = ErrorCodes.IGNORED_ALL_NOTIFICATIONS)

class PrintSupportFileNotFound(IPPClientException):
    ipp_error_code = ErrorCodes.PRINT_SUPPORT_FILE_NOT_FOUND)

### Server error codes

class InternalError(IPPServerException):
    ipp_error_code = ErrorCodes.INTERNAL_ERROR)

class OperationNotSupported(IPPServerException):
    ipp_error_code = ErrorCodes.OPERATION_NOT_SUPPORTED)

class ServiceUnavailable(IPPServerException):
    ipp_error_code = ErrorCodes.SERVICE_UNAVAILABLE)

class VersionNotSupported(IPPServerException):
    ipp_error_code = ErrorCodes.VERSION_NOT_SUPPORTED)

class DeviceError(IPPServerException):
    ipp_error_code = ErrorCodes.DEVICE_ERROR)

class TemporaryError(IPPServerException):
    ipp_error_code = ErrorCodes.TEMPORARY_ERROR)

class NotAccepting(IPPServerException):
    ipp_error_code = ErrorCodes.NOT_ACCEPTING)

class PrinterBusy(IPPServerException):
    ipp_error_code = ErrorCodes.PRINTER_BUSY)

class ErrorJobCancelled(IPPServerException):
    ipp_error_code = ErrorCodes.ERROR_JOB_CANCELLED)

class MultipleJobsNotSupported(IPPServerException):
    ipp_error_code = ErrorCodes.MULTIPLE_JOBS_NOT_SUPPORTED)

class PrinterIsDeactivated(IPPServerException):
    ipp_error_code = ErrorCodes.PRINTER_IS_DEACTIVATED)
