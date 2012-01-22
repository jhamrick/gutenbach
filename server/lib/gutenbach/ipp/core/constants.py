__all__ = [
    'JobStates',
    'PrinterStates',
    'OperationCodes',
    'SuccessCodes',
    'ClientErrorCodes',
    'ServerErrorCodes',
    'ErrorCodes',
    'StatusCodes',
    'CUPSPrinterType',
    'AttributeTags',
    'OutOfBandTags',
    'IntegerTags',
    'OctetStringTags',
    'CharacterStringTags',
]

class JobStates():
    """Job state codes, as defined by RFC 2911, Section 4.3.7
    
    """

    PENDING            = 3
    PENDING_HELD       = 4
    PROCESSING         = 5
    PROCESSING_STOPPED = 6
    CANCELED           = 7
    ABORTED            = 8
    COMPLETED          = 9

    def __init__(self): pass

class PrinterStates():
    """Printer state codes, as defined by RFC 2911, Section 4.4.11
    
    """

    IDLE       = 3
    PROCESSING = 4
    STOPPED    = 5

    def __init__(self): pass

class OperationCodes():
    """IPP and CUPS IPP Operations, as defined in various RFCs:

        0x0002 - 0x0012      RFC 2911 (Section 4.4.15)
        0x0013 - 0x0015      RFC 3380 (Section 4)
        0x0016 - 0x001b      RFC 3995 (Section 7.1)
        0x0022 - 0x0031      RFC 3998 (Section 14.3)
        0x4000 - 0x4027      CUPS IPP Actions
        
    """

    # These are defined in RFC 2911, Section 4.4.15
    PRINT_JOB              = 0x0002
    PRINT_URI              = 0x0003
    VALIDATE_JOB           = 0x0004
    CREATE_JOB             = 0x0005
    SEND_DOCUMENT          = 0x0006
    SEND_URI               = 0x0007
    CANCEL_JOB             = 0x0008
    GET_JOB_ATTRIBUTES     = 0x0009
    GET_JOBS               = 0x000a
    GET_PRINTER_ATTRIBUTES = 0x000b
    #HOLD_JOB              = 0x000c
    #RELEASE_JOB           = 0x000d
    RESTART_JOB            = 0x000e
    PAUSE_PRINTER          = 0x0010
    RESUME_PRINTER         = 0x0011
    #PURGE_JOBS            = 0x0012

    # These are defined in RFC 3380, Section 4
    SET_PRINTER_ATTRIBUTES           = 0x0013
    SET_JOB_ATTRIBUTES               = 0x0014
    #GET_PRINTER_SUPPORTED_VALUES    = 0x0015

    # These are defined in RFC 3995, Section 7.1
    #CREATE_PRINTER_SUBSCRIPTION     = 0x0016
    #CREATE_JOB_SUBSCRIPTION         = 0x0017
    #GET_SUBSCRIPTION_ATTRIBUTES     = 0x0018
    #GET_SUBSCRIPTIONS               = 0x0019
    #RENEW_SUBSCRIPTION              = 0x001a
    #CANCEL_SUBSCRIPTION             = 0x001b

    # These are defined in RFC 3998, Section 14.3
    #ENABLE_PRINTER                  = 0x0022
    #DISABLE_PRINTER                 = 0x0023
    #PAUSE_PRINTER_AFTER_CURRENT_JOB = 0x0024
    #HOLD_NEW_JOBS                   = 0x0025
    #RELEASE_HELD_NEW_JOBS           = 0x0026
    #DEACTIVATE_PRINTER              = 0x0027
    #ACTIVATE_PRINTER                = 0x0028
    #RESTART_PRINTER                 = 0x0029
    #SHUTDOWN_PRINTER                = 0x002a
    #STARTUP_PRINTER                 = 0x002b
    #REPROCESS_JOB                   = 0x002c
    #CANCEL_CURRENT_JOB              = 0x002d
    #SUSPEND_CURRENT_JOB             = 0x002e
    #RESUME_JOB                      = 0x002f
    PROMOTE_JOB                      = 0x0030
    #SCHEDULE_JOB_AFTER              = 0x0031

    # These are special CUPS actions, defined in:
    # http://www.cups.org/documentation.php/spec-ipp.html
    #PRIVATE               = 0x4000
    CUPS_GET_DEFAULT       = 0x4001
    CUPS_GET_PRINTERS      = 0x4002
    #CUPS_ADD_PRINTER      = 0x4003
    #CUPS_DELETE_PRINTER   = 0x4004
    CUPS_GET_CLASSES       = 0x4005
    #CUPS_ADD_CLASS        = 0x4006
    #CUPS_DELETE_CLASS     = 0x4007
    #CUPS_ACCEPT_JOBS      = 0x4008
    #CUPS_REJECT_JOBS      = 0x4009
    #CUPS_SET_DEFAULT      = 0x400a
    #CUPS_GET_DEVICES      = 0x400b
    #CUPS_GET_PPDS         = 0x400c
    #CUPS_MOVE_JOB         = 0x400d
    #CUPS_AUTHENTICATE_JOB = 0x400e
    #CUPS_GET_PPD          = 0x400f
    CUPS_GET_DOCUMENT      = 0x4027

    def __init__(self): pass

class SuccessCodes():
    """Success status codes as defined in RFC 2911, Section 13
    
    """
    
    OK                           = 0x0000
    OK_SUBST                     = 0x0001
    OK_CONFLICT                  = 0x0002
    OK_IGNORED_SUBSCRIPTIONS     = 0x0003
    OK_IGNORED_NOTIFICATIONS     = 0x0004
    OK_TOO_MANY_EVENTS           = 0x0005
    OK_BUT_CANCEL_SUBSCRIPTION   = 0x0006

    def __init__(self): pass

class ClientErrorCodes():
    """Client error codes as defined in RFC 2911, Section 13
    
    """
    
    BAD_REQUEST                  = 0x0400
    FORBIDDEN                    = 0x0401
    NOT_AUTHENTICATED            = 0x0402
    NOT_AUTHORIZED               = 0x0403
    NOT_POSSIBLE                 = 0x0404
    TIMEOUT                      = 0x0405
    NOT_FOUND                    = 0x0406
    GONE                         = 0x0407
    REQUEST_ENTITY               = 0x0408
    REQUEST_VALUE                = 0x0409
    DOCUMENT_FORMAT              = 0x040a
    ATTRIBUTES                   = 0x040b
    URI_SCHEME                   = 0x040c
    CHARSET                      = 0x040d
    CONFLICT                     = 0x040e
    COMPRESSION_NOT_SUPPORTED    = 0x040f
    COMPRESSION_ERROR            = 0x0410
    DOCUMENT_FORMAT_ERROR        = 0x0411
    DOCUMENT_ACCESS_ERROR        = 0x0412
    ATTRIBUTES_NOT_SETTABLE      = 0x0413
    IGNORED_ALL_SUBSCRIPTIONS    = 0x0414
    TOO_MANY_SUBSCRIPTIONS       = 0x0415
    IGNORED_ALL_NOTIFICATIONS    = 0x0416
    PRINT_SUPPORT_FILE_NOT_FOUND = 0x0417

    def __init__(self): pass

class ServerErrorCodes():
    """Server error codes as defined in RFC 2911, Section 13
    
    """

    INTERNAL_ERROR              = 0x0500
    OPERATION_NOT_SUPPORTED     = 0x0501
    SERVICE_UNAVAILABLE         = 0x0502
    VERSION_NOT_SUPPORTED       = 0x0503
    DEVICE_ERROR                = 0x0504
    TEMPORARY_ERROR             = 0x0505
    NOT_ACCEPTING               = 0x0506
    PRINTER_BUSY                = 0x0507
    ERROR_JOB_CANCELLED         = 0x0508
    MULTIPLE_JOBS_NOT_SUPPORTED = 0x0509
    PRINTER_IS_DEACTIVATED      = 0x050a

    def __init__(self): pass

class StatusCodes(SuccessCodes, ClientErrorCodes, ServerErrorCodes):
    pass
class ErrorCodes(ClientErrorCodes, ServerErrorCodes):
    pass

class CUPSPrinterType():
    """Printer types as defined by cups_ptype_e in the CUPS API
    specification:
    
    http://www.cups.org/documentation.php/doc-1.3/api-cups.html#cups_ptype_e
    
    """

    LOCAL         = 0x000000
    CLASS         = 0x000001
    REMOTE        = 0x000002
    BW            = 0x000004
    COLOR         = 0x000008

    DUPLEX        = 0x000010
    STAPLE        = 0x000020
    COPIES        = 0x000040
    COLLATE       = 0x000080

    PUNCH         = 0x000100
    COVER         = 0x000200
    BIND          = 0x000400
    SORT          = 0x000800

    SMALL         = 0x001000
    MEDIUM        = 0x002000
    LARGE         = 0x004000
    VARIABLE      = 0x008000

    IMPLICIT      = 0x010000
    DEFAULT       = 0x020000
    FAX           = 0x040000
    REJECTING     = 0x080000

    DELETE        = 0x100000
    NOT_SHARED    = 0x200000
    AUTHENTICATED = 0x400000
    COMMANDS      = 0x800000

    OPTIONS       = 0x00e6ff

    def __init__(self): pass

class AttributeTags():
    """Contains constants for the attribute IPP tags, as defined by
    RFC 2565.
    
    """
    
    ZERO_NAME_LENGTH   = 0x00
    OPERATION          = 0x01
    JOB                = 0x02
    END                = 0x03
    PRINTER            = 0x04
    UNSUPPORTED        = 0x05
    SUBSCRIPTION       = 0x06
    EVENT_NOTIFICATION = 0x07

    def __init__(self): pass

class OutOfBandTags():
    """Contains constants for the out-of-band value IPP tags, as
    defined by RFC 2565.
    
    """
    
    UNSUPPORTED      = 0x10
    DEFAULT          = 0x11
    UNKNOWN          = 0x12
    NO_VALUE         = 0x13
    NOT_SETTABLE     = 0x15
    DELETE_ATTRIBUTE = 0x16
    ADMIN_DEFINE     = 0x17

    def __init__(self): pass

class IntegerTags():
    """Contains constants for the integer value IPP tags, as defined
    by RFC 2565.
    
    """
    
    GENERIC = 0x20
    INTEGER = 0x21
    BOOLEAN = 0x22
    ENUM    = 0x23

    def __init__(self): pass

class OctetStringTags():
    """Contains constants for the octetString value IPP tags, as
    defined by RFC 2565.
    
    """
    
    UNSPECIFIED_OCTETSTRING = 0x30
    DATETIME                = 0x31
    RESOLUTION              = 0x32
    RANGE_OF_INTEGER        = 0x33
    BEG_COLLECTION          = 0x34
    TEXT_WITH_LANGUAGE      = 0x35
    NAME_WITH_LANGUAGE      = 0x36
    END_COLLECTION          = 0x37

    def __init__(self): pass

class CharacterStringTags():
    """Contains constants for the character-string value IPP tags, as
    defined by RFC 2565.
    
    """
    
    GENERIC               = 0x40
    TEXT_WITHOUT_LANGUAGE = 0x41
    NAME_WITHOUT_LANGUAGE = 0x42
    KEYWORD               = 0x44
    URI                   = 0x45
    URI_SCHEME            = 0x46
    CHARSET               = 0x47
    NATURAL_LANGUAGE      = 0x48
    MIME_MEDIA_TYPE       = 0x49                                    
    MEMBER_ATTR_NAME      = 0x4a
