from .constants import ErrorCodes

def error_code(func):
    def set_code(val):
        func.error_code = val
        return func
    return set_code

class IPPException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message

### Client error codes
    
@error_code(ErrorCodes.BAD_REQUEST)
class BadRequest(IPPException):
    pass

@error_code(ErrorCodes.FORBIDDEN)
class Forbidden(IPPException):
    pass

@error_code(ErrorCodes.NOT_AUTHENTICATED)
class NotAuthenticated(IPPException):
    pass

@error_code(ErrorCodes.NOT_AUTHORIZED)
class NotAuthorized(IPPException):
    pass

@error_code(ErrorCodes.NOT_POSSIBLE)
class NotPossible(IPPException):
    pass

@error_code(ErrorCodes.TIMEOUT)
class Timeout(IPPException):
    pass

@error_code(ErrorCodes.NOT_FOUND)
class NotFound(IPPException):
    pass

@error_code(ErrorCodes.GONE)
class Gone(IPPException):
    pass

@error_code(ErrorCodes.REQUEST_ENTITY)
class RequestEntity(IPPException):
    pass

@error_code(ErrorCodes.REQUEST_VALUE)
class RequestValue(IPPException):
    pass

@error_code(ErrorCodes.DOCUMENT_FORMAT)
class DocumentFormat(IPPException):
    pass

@error_code(ErrorCodes.ATTRIBUTES)
class Attributes(IPPException):

    def __init__(self, message, attrs):
        self.message = message
        self.bad_attrs = attrs

@error_code(ErrorCodes.URI_SCHEME)
class UriScheme(IPPException):
    pass

@error_code(ErrorCodes.CHARSET)
class Charset(IPPException):
    pass

@error_code(ErrorCodes.CONFLICT)
class Conflict(IPPException):
    pass

@error_code(ErrorCodes.COMPRESSION_NOT_SUPPORTED)
class CompressionNotSupported(IPPException):
    pass

@error_code(ErrorCodes.COMPRESSION_ERROR)
class CompressionError(IPPException):
    pass

@error_code(ErrorCodes.DOCUMENT_FORMAT_ERROR)
class DocumentFormatError(IPPException):
    pass

@error_code(ErrorCodes.DOCUMENT_ACCESS_ERROR)
class DocumentAccessError(IPPException):
    pass

@error_code(ErrorCodes.ATTRIBUTES_NOT_SETTABLE)
class AttributesNotSettable(IPPException):
    pass

@error_code(ErrorCodes.IGNORED_ALL_SUBSCRIPTIONS)
class IgnoredAllSubscriptions(IPPException):
    pass

@error_code(ErrorCodes.TOO_MANY_SUBSCRIPTIONS)
class TooManySubscriptions(IPPException):
    pass

@error_code(ErrorCodes.IGNORED_ALL_NOTIFICATIONS)
class IgnoredAllNotifications(IPPException):
    pass

@error_code(ErrorCodes.PRINT_SUPPORT_FILE_NOT_FOUND)
class PrintSupportFileNotFound(IPPException):
    pass


### Server error codes

@error_code(ErrorCodes.INTERNAL_ERROR)
class InternalError(IPPException):
    pass

@error_code(ErrorCodes.OPERATION_NOT_SUPPORTED)
class OperationNotSupported(IPPException):
    pass

@error_code(ErrorCodes.SERVICE_UNAVAILABLE)
class ServiceUnavailable(IPPException):
    pass

@error_code(ErrorCodes.VERSION_NOT_SUPPORTED)
class VersionNotSupported(IPPException):
    pass

@error_code(ErrorCodes.DEVICE_ERROR)
class DeviceError(IPPException):
    pass

@error_code(ErrorCodes.TEMPORARY_ERROR)
class TemporaryError(IPPException):
    pass

@error_code(ErrorCodes.NOT_ACCEPTING)
class NotAccepting(IPPException):
    pass

@error_code(ErrorCodes.PRINTER_BUSY)
class PrinterBusy(IPPException):
    pass

@error_code(ErrorCodes.ERROR_JOB_CANCELLED)
class ErrorJobCancelled(IPPException):
    pass

@error_code(ErrorCodes.MULTIPLE_JOBS_NOT_SUPPORTED)
class MultipleJobsNotSupported(IPPException):
    pass

@error_code(ErrorCodes.PRINTER_IS_DEACTIVATED)
class PrinterIsDeactivated(IPPException):
    pass
