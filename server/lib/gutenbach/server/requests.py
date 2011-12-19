from gutenbach.server.exceptions import MalformedIPPRequestException
from gutenbach.server.printer import GutenbachPrinter
import gutenbach.ipp as ipp
import gutenbach.ipp.constants as const
import logging

# initialize logger
logger = logging.getLogger(__name__)

def handler_for(operation):
    """A decorator method to mark a function with the operation id
    that it handles.  This value will be stored in
    'func.ipp_operation'.

    """
    
    def f(func):
        func.ipp_operation = operation
        return func
    return f

class GutenbachRequestHandler(object):

    def __init__(self):
        self.printers = {
            "test": GutenbachPrinter(name="test")
            }
        self.default = "test"
    
    def handle(self, request, response):
        # look up the handler
        handler = None
        handler_name = None
        for d in dir(self):
            if getattr(getattr(self, d), "ipp_operation", None) == request.operation_id:
                handler_name = d
                break
        # we couldn't find a handler, so default to unknown operation
        if handler_name is None:
            handler_name = "unknown_operation"
        # call the handler
        handler = getattr(self, handler_name)
        logger.info("Handling request of type '%s'" % handler_name)
        handler(request, response)

    def unknown_operation(self, request, response):
        logger.warning("Received unknown operation 0x%x" % request.operation_id)
        response.operation_id = const.StatusCodes.OPERATION_NOT_SUPPORTED

    ##### Helper functions

    def _get_printer_attributes(self, printer, request, response):
        response.attribute_groups.append(ipp.AttributeGroup(
            const.AttributeTags.PRINTER,
            printer.get_printer_attributes(request)))

    def _get_job_attributes(self, job_id, printer, request, response):
        response.attribute_groups.append(ipp.AttributeGroup(
            const.AttributeTags.JOB,
            job.get_job_attributes(request)))

    def _get_printer_name(self, request):
        # make sure the first group is an OPERATION group
        group_tag = request.attribute_groups[0].tag
        if group_tag != const.AttributeTags.OPERATION:
            raise MalformedIPPRequestException, \
                  "Expected OPERATION group tag, got %d\n", group_tag

        # make sure the printer-uri value is appropriate
        printer_name_attr = request.attribute_groups[0]['printer-uri']
        printer_name_value_tag = printer_name_attr.values[0].value_tag
        if printer_name_value_tag != const.CharacterStringTags.URI:
            raise MalformedIPPRequestException, \
                  "Expected URI value tag, got %s" % printer_name_value_tag

        # actually get the printer name
        printer_name_value = printer_name_attr.values[0].value
        # XXX: hack -- CUPS will strip the port from the request, so
        # we can't do an exact comparison (also the hostname might be
        # different, depending on the CNAME or whether it's localhost)
        printer_name = printer_name_value.split("/")[-1]

        # make sure the printer name is valid
        if printer_name not in self.printers:
            raise ValueError, "Invalid printer uri: %s" % printer_name_value

        return printer_name

    def _get_job_id(self, request):
        pass
        
    ##### Printer Commands

    def print_job(self, request, response):
        pass

    def validate_job(self, request, response):
        pass

    @handler_for(const.Operations.GET_JOBS)
    def get_jobs(self, request, response):
        printer_name = self._get_printer_name(request)
        # Each job will append a new job attribute group.
        for job in self.printers[printer_name].get_jobs():
            self._get_job_attributes(job, request, response)

    def print_uri(self, request, response):
        pass

    def create_job(self, request, response):
        pass

    def pause_printer(self, request, response):
        pass

    def resume_printer(self, request, response):
        pass

    @handler_for(const.Operations.GET_PRINTER_ATTRIBUTES)
    def get_printer_attributes(self, request, response):
        # this is just like cups_get_default, except the printer name
        # is given
        printer_name = self._get_printer_name(request)
        self._get_printer_attributes(self.printers[printer_name], request, response)

    def set_printer_attributes(self, request, response):
        pass

    ##### Job Commands

    def cancel_job(self, request, response):
        pass

    def send_document(self, request, response):
        pass

    def send_uri(self, request, response):
        pass

    def get_job_attributes(self, request, response):
        printer_name = self._get_printer_name(request)
        job_id = self._get_job_id(request)
        self._get_job_attributes(
            self.printers[printer_name].get_job(job_id), request, response)

    def set_job_attributes(self, request, response):
        pass

    def cups_get_document(self, request, response):
        pass

    def restart_job(self, request, response):
        pass

    def promote_job(self, request, response):
        pass


    ##### CUPS Specific Commands

    @handler_for(const.Operations.CUPS_GET_DEFAULT)
    def cups_get_default(self, request, response):
        """The CUPS-Get-Default operation (0x4001) returns the default
        printer URI and attributes.

        CUPS-Get-Default Request
        ------------------------

        The following groups of attributes are supplied as part of the
        CUPS-Get-Default request:

        Group 1: Operation Attributes
            Natural Language and Character Set:
                The 'attributes-charset' and
                'attributes-natural-language' attributes as described
                in section 3.1.4.1 of the IPP Model and Semantics
                document.
            'requested-attributes' (1setOf keyword):
                The client OPTIONALLY supplies a set of attribute
                names and/or attribute group names in whose values the
                requester is interested. If the client omits this
                attribute, the server responds as if this attribute
                had been supplied with a value of 'all'.
        
        CUPS-Get-Default Response
        -------------------------

        The following groups of attributes are send as part of the
        CUPS-Get-Default Response:

        Group 1: Operation Attributes
            Status Message:
                The standard response status message.
            Natural Language and Character Set:
                The 'attributes-charset' and
                'attributes-natural-language' attributes as described
                in section 3.1.4.2 of the IPP Model and Semantics
                document.

        Group 2: Printer Object Attributes
            The set of requested attributes and their current values.

        (Source: http://www.cups.org/documentation.php/spec-ipp.html#CUPS_GET_DEFAULT )

        """
            
        self._get_printer_attributes(self.printers[self.default], request, response)

    @handler_for(const.Operations.CUPS_GET_PRINTERS)
    def cups_get_printers(self, request, response):
        """
        The CUPS-Get-Printers operation (0x4002) returns the printer
        attributes for every printer known to the system. This may
        include printers that are not served directly by the server.

        CUPS-Get-Printers Request
        -------------------------
        
        The following groups of attributes are supplied as part of the
        CUPS-Get-Printers request:

        Group 1: Operation Attributes
            Natural Language and Character Set:
                The 'attributes-charset' and
                'attributes-natural-language' attributes as described
                in section 3.1.4.1 of the IPP Model and Semantics
                document.
            'first-printer-name' (name(127)):CUPS 1.2/Mac OS X 10.5
                The client OPTIONALLY supplies this attribute to
                select the first printer that is returned.
            'limit' (integer (1:MAX)):
                The client OPTIONALLY supplies this attribute limiting
                the number of printers that are returned.
            'printer-location' (text(127)): CUPS 1.1.7
                The client OPTIONALLY supplies this attribute to
                select which printers are returned.
            'printer-type' (type2 enum): CUPS 1.1.7
                The client OPTIONALLY supplies a printer type
                enumeration to select which printers are returned.
            'printer-type-mask' (type2 enum): CUPS 1.1.7
                The client OPTIONALLY supplies a printer type mask
                enumeration to select which bits are used in the
                'printer-type' attribute.
            'requested-attributes' (1setOf keyword) :
                The client OPTIONALLY supplies a set of attribute
                names and/or attribute group names in whose values the
                requester is interested. If the client omits this
                attribute, the server responds as if this attribute
                had been supplied with a value of 'all'.
            'requested-user-name' (name(127)) : CUPS 1.2/Mac OS X 10.5
                The client OPTIONALLY supplies a user name that is
                used to filter the returned printers.

        CUPS-Get-Printers Response
        --------------------------

        The following groups of attributes are send as part of the
        CUPS-Get-Printers Response:

        Group 1: Operation Attributes
            Status Message:
                The standard response status message.
            Natural Language and Character Set:
                The 'attributes-charset' and
                'attributes-natural-language' attributes as described
                in section 3.1.4.2 of the IPP Model and Semantics
                document.
                
        Group 2: Printer Object Attributes
            The set of requested attributes and their current values
            for each printer.

        (Source: http://www.cups.org/documentation.php/spec-ipp.html#CUPS_GET_PRINTERS )
            
        """

        # Each printer will append a new printer attribute group.
        for printer in self.printers:
            self._get_printer_attributes(self.printers[printer], request, response)

    @handler_for(const.Operations.CUPS_GET_CLASSES)
    def cups_get_classes(self, request, response):
        """The CUPS-Get-Classes operation (0x4005) returns the printer
        attributes for every printer class known to the system. This
        may include printer classes that are not served directly by
        the server.

        CUPS-Get-Classes Request
        ------------------------

        The following groups of attributes are supplied as part of the
        CUPS-Get-Classes request:

        Group 1: Operation Attributes
            Natural Language and Character Set:
                The 'attributes-charset' and
                'attributes-natural-language' attributes as described
                in section 3.1.4.1 of the IPP Model and Semantics
                document.
            'first-printer-name' (name(127)):CUPS 1.2/Mac OS X 10.5
                The client OPTIONALLY supplies this attribute to
                select the first printer that is returned.
            'limit' (integer (1:MAX)):
                The client OPTIONALLY supplies this attribute limiting
                the number of printer classes that are returned.
            'printer-location' (text(127)): CUPS 1.1.7
                The client OPTIONALLY supplies this attribute to
                select which printer classes are returned.
            'printer-type' (type2 enum): CUPS 1.1.7
                The client OPTIONALLY supplies a printer type
                enumeration to select which printer classes are
                returned.
            'printer-type-mask' (type2 enum): CUPS 1.1.7
                The client OPTIONALLY supplies a printer type mask
                enumeration to select which bits are used in the
                'printer-type' attribute.
            'requested-attributes' (1setOf keyword) :
                The client OPTIONALLY supplies a set of attribute
                names and/or attribute group names in whose values the
                requester is interested. If the client omits this
                attribute, the server responds as if this attribute
                had been supplied with a value of 'all'.
            'requested-user-name' (name(127)) : CUPS 1.2/Mac OS X 10.5
                The client OPTIONALLY supplies a user name that is
                used to filter the returned printers.
                
        CUPS-Get-Classes Response
        -------------------------

        The following groups of attributes are send as part of the
        CUPS-Get-Classes Response:

        Group 1: Operation Attributes
            Status Message:
                The standard response status message.
            Natural Language and Character Set:
                The 'attributes-charset' and
                'attributes-natural-language' attributes as described
                in section 3.1.4.2 of the IPP Model and Semantics
                document.

        Group 2: Printer Class Object Attributes
            The set of requested attributes and their current values
            for each printer class.

        (Source: http://www.cups.org/documentation.php/spec-ipp.html#CUPS_GET_CLASSES )

        """
        
        # We have no printer classes, so we don't need to do anything
        pass
