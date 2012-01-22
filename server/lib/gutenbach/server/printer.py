from . import sync
from .errors import InvalidJobException, InvalidPrinterStateException, InvalidJobStateException
from .job import GutenbachJob
from gutenbach.ipp import PrinterStates as States
import gutenbach.ipp as ipp
import logging
import math
import sys
import tempfile
import threading
import time
import traceback

# initialize logger
logger = logging.getLogger(__name__)

class GutenbachPrinter(threading.Thread):

    # for IPP
    printer_attributes = [
        "printer-uri-supported",
        "uri-authentication-supported",
        "uri-security-supported",
        "printer-name",
        "printer-state",
        "printer-state-reasons",
        "ipp-versions-supported",
        "operations-supported",
        "charset-configured",
        "charset-supported",
        "natural-language-configured",
        "generated-natural-language-supported",
        "document-format-default",
        "document-format-supported",
        "printer-is-accepting-jobs",
        "queued-job-count",
        "pdl-override-supported",
        "printer-up-time",
        "compression-supported",
        "multiple-operation-time-out",
        "multiple-document-jobs-supported",
    ]

    job_attributes = [
        "job-id",
        "job-name",
        "job-originating-user-name",
        "job-k-octets",
        "job-state",
        "job-printer-uri"
    ]

    operations = [
        "print-job",
        "validate-job",
        "get-jobs",
        "print-uri",
        "create-job",
        "pause-printer",
        "resume-printer",
        "get-printer-attributes",
        "set-printer-attributes",
        "cancel-job",
        "send-document",
        "send-uri",
        "get-job-attributes",
        "set-job-attributes",
        "restart-job",
        "promote-job"
    ]
        
    def __init__(self, name, config, *args, **kwargs):

        super(GutenbachPrinter, self).__init__(*args, **kwargs)
        
        self.name = name
        self.config = config
        self.time_created = int(time.time())

        self.finished_jobs = []
        self.pending_jobs = []
        self.current_job = None
        self.jobs = {}

        self.lock = threading.RLock()
        self._running = False
        self.paused = False

        # CUPS ignores jobs with id 0, so we have to start at 1
        self._next_job_id = 1

    @sync
    def __repr__(self):
        return str(self)

    @sync
    def __str__(self):
        return "<Printer '%s'>" % self.name

    def run(self):
        self._running = True
        while self._running:
            with self.lock:
                try:
                    if self.current_job is None:
                        self.start_job()
                    elif self.current_job.is_done:
                        self.complete_job()
                except:
                    self._running = False
                    logger.fatal(traceback.format_exc())
                    break
            time.sleep(0.1)

    def stop(self):
        with self.lock:
            for job in self.jobs.keys():
                try:
                    self.jobs[job].abort()
                    del self.jobs[job]
                except InvalidJobStateException:
                    pass
                
            self._running = False
        if self.ident is not None and self.isAlive():
            self.join()

    ######################################################################
    ###                          Properties                            ###
    ######################################################################

    @property
    def name(self):
        return self._name
    @name.setter
    def name(self, val):
        try:
            self._name = str(val)
        except:
            self._name = "gutenbach-printer"

    @property
    def config(self):
        return self._config
    @config.setter
    def config(self, val):
        try:
            _config = dict(val).copy()
        except:
            raise ValueError, "not a dictionary"
        if 'ipp-versions' not in _config:
            raise ValueError, "missing ipp-versions"
        self._config = _config

    @property
    def uris(self):
        uris = ["ipp://localhost:8000/printers/" + self.name,
                "ipp://localhost/printers/" + self.name]
        return uris
    
    @property
    def uri(self):
        return self.uris[0]

    @property
    @sync
    def state(self):
        if self.is_running and not self.paused:
            if len(self.active_jobs) > 0:
                state = States.PROCESSING
            else:
                state = States.IDLE
        else:
            state = States.STOPPED

        return state

    @property
    @sync
    def active_jobs(self):
        jobs = self.pending_jobs[:]
        if self.current_job is not None:
            jobs.insert(0, self.current_job.id)
        return jobs

    @property
    def is_running(self):
        running = self.ident is not None and self.isAlive() and self._running
        return running

    ######################################################################
    ###                            Methods                             ###
    ######################################################################

    @sync
    def assert_running(self):
        if not self.is_running:
            raise RuntimeError, "%s not started" % str(self)

    @sync
    def start_job(self):
        self.assert_running()
        if not self.paused and self.current_job is None:
            try:
                job_id = self.pending_jobs.pop(0)
                self.current_job = self.get_job(job_id)
                self.current_job.play()
            except IndexError:
                self.current_job = None
                    
    @sync
    def complete_job(self):
        self.assert_running()
        if not self.paused and self.current_job is not None:
            try:
                if not self.current_job.is_done:
                    self.current_job.stop()
            finally:
                self.finished_jobs.append(self.current_job.id)
                self.current_job = None

    @sync
    def get_job(self, job_id):
        self.assert_running()
        if job_id not in self.jobs:
            raise InvalidJobException(job_id)
        return self.jobs[job_id]

    ######################################################################
    ###                        IPP Attributes                          ###
    ######################################################################

    @property
    def printer_uri_supported(self):
        """RFC 2911: 4.4.1 printer-uri-supported (1setOf uri)

        This REQUIRED Printer attribute contains at least one URI for
        the Printer object.  It OPTIONALLY contains more than one URI
        for the Printer object.  An administrator determines a Printer
        object's URI(s) and configures this attribute to contain those
        URIs by some means outside the scope of this IPP/1.1 document.
        The precise format of this URI is implementation dependent and
        depends on the protocol.  See the next two sections for a
        description of the 'uri-security-supported' and
        'uri-authentication-supported' attributes, both of which are
        the REQUIRED companion attributes to this 'printer-uri-
        supported' attribute.  See section 2.4 on Printer object
        identity and section 8.2 on security and URIs for more
        information.

        """
        self.assert_running()
        return ipp.PrinterUriSupported(self.uri)
    @printer_uri_supported.setter
    def printer_uri_supported(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("printer-uri-supported")

    @property
    def uri_authentication_supported(self):
        """RFC 2911: 4.4.2 uri-authentication-supported (1setOf type2
        keyword)

        This REQUIRED Printer attribute MUST have the same cardinality
        (contain the same number of values) as the
        'printer-uri-supported' attribute.  This attribute identifies
        the Client Authentication mechanism associated with each URI
        listed in the 'printer-uri- supported' attribute. The Printer
        object uses the specified mechanism to identify the
        authenticated user (see section 8.3).  The 'i th' value in
        'uri-authentication-supported' corresponds to the 'i th' value
        in 'printer-uri-supported' and it describes the authentication
        mechanisms used by the Printer when accessed via that URI.
        See [RFC2910] for more details on Client Authentication.

        The following standard keyword values are defined:
        
        'none': There is no authentication mechanism associated with
            the URI.  The Printer object assumes that the
            authenticated user is 'anonymous'.

        'requesting-user-name': When a client performs an operation
            whose target is the associated URI, the Printer object
            assumes that the authenticated user is specified by the
            'requesting-user- name' Operation attribute (see section
            8.3). If the 'requesting-user-name' attribute is absent in
            a request, the Printer object assumes that the
            authenticated user is 'anonymous'.

        'basic': When a client performs an operation whose target is
            the associated URI, the Printer object challenges the
            client with HTTP basic authentication [RFC2617]. The
            Printer object assumes that the authenticated user is the
            name received via the basic authentication mechanism.

        'digest': When a client performs an operation whose target is
            the associated URI, the Printer object challenges the
            client with HTTP digest authentication [RFC2617]. The
            Printer object assumes that the authenticated user is the
            name received via the digest authentication mechanism.

        'certificate': When a client performs an operation whose
            target is the associated URI, the Printer object expects
            the client to provide a certificate. The Printer object
            assumes that the authenticated user is the textual name
            contained within the certificate.

        """
        self.assert_running()
        return ipp.UriAuthenticationSupported("none")
    @uri_authentication_supported.setter
    def uri_authentication_supported(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("uri-authentication-supported")

    @property
    def uri_security_supported(self):
        """RFC 2911: 4.4.3 uri-security-supported (1setOf type2
        keyword)
        
        This REQUIRED Printer attribute MUST have the same cardinality
        (contain the same number of values) as the
        'printer-uri-supported' attribute. This attribute identifies
        the security mechanisms used for each URI listed in the
        'printer-uri-supported' attribute. The 'i th' value in
        'uri-security-supported' corresponds to the 'i th' value in
        'printer-uri-supported' and it describes the security
        mechanisms used for accessing the Printer object via that
        URI. See [RFC2910] for more details on security mechanisms.

        The following standard keyword values are defined:

            'none': There are no secure communication channel
                    protocols in use for the given URI.

            'ssl3': SSL3 [SSL] is the secure communications channel
                    protocol in use for the given URI.

            'tls':  TLS [RFC2246] is the secure communications channel
                    protocol in use for the given URI.

        This attribute is orthogonal to the definition of a Client
        Authentication mechanism. Specifically, 'none' does not
        exclude Client Authentication. See section 4.4.2.

        Consider the following example. For a single Printer object,
        an administrator configures the 'printer-uri-supported', 'uri-
        authentication-supported' and 'uri-security-supported'
        attributes as follows:

        'printer-uri-supported': 'xxx://acme.com/open-use-printer',
            'xxx://acme.com/restricted-use-printer',
            'xxx://acme.com/private-printer'
        'uri-authentication-supported': 'none', 'digest', 'basic'
        'uri-security-supported': 'none', 'none', 'tls'

        Note: 'xxx' is not a valid scheme. See the IPP/1.1 'Transport
        and Encoding' document [RFC2910] for the actual URI schemes to
        be used in object target attributes.

        In this case, one Printer object has three URIs.

        - For the first URI, 'xxx://acme.com/open-use-printer', the
          value 'none' in 'uri-security-supported' indicates that
          there is no secure channel protocol configured to run under
          HTTP. The value of 'none' in 'uri-authentication-supported'
          indicates that all users are 'anonymous'. There will be no
          challenge and the Printer will ignore
          'requesting-user-name'.

        - For the second URI, 'xxx://acme.com/restricted-use-printer',
          the value 'none' in 'uri-security-supported' indicates that
          there is no secure channel protocol configured to run under
          HTTP. The value of 'digest' in
          'uri-authentication-supported' indicates that the Printer
          will issue a challenge and that the Printer will use the
          name supplied by the digest mechanism to determine the
          authenticated user (see section 8.3).

        - For the third URI, 'xxx://acme.com/private-printer', the
          value 'tls' in 'uri-security-supported' indicates that TLS
          is being used to secure the channel. The client SHOULD be
          prepared to use TLS framing to negotiate an acceptable
          ciphersuite to use while communicating with the Printer
          object. In this case, the name implies the use of a secure
          communications channel, but the fact is made explicit by the
          presence of the 'tls' value in 'uri-security-supported'. The
          client does not need to resort to understanding which
          security it must use by following naming conventions or by
          parsing the URI to determine which security mechanisms are
          implied. The value of 'basic' in 'uri-
          authentication-supported' indicates that the Printer will
          issue a challenge and that the Printer will use the name
          supplied by the digest mechanism to determine the
          authenticated user (see section 8.3). Because this challenge
          occurs in a tls session, the channel is secure.

        It is expected that many IPP Printer objects will be
        configured to support only one channel (either configured to
        use TLS access or not) and only one authentication
        mechanism. Such Printer objects only have one URI listed in
        the 'printer-uri-supported' attribute. No matter the
        configuration of the Printer object (whether it has only one
        URI or more than one URI), a client MUST supply only one URI
        in the target 'printer-uri' operation attribute.

        """
        
        self.assert_running()
        return ipp.UriSecuritySupported("none")
    @uri_security_supported.setter
    def uri_security_supported(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("uri-security-supported")

    @property
    def printer_name(self):
        """RFC 2911: 4.4.4 printer-name (name(127))
        
        This REQUIRED Printer attribute contains the name of the
        Printer object. It is a name that is more end-user friendly
        than a URI. An administrator determines a printer's name and
        sets this attribute to that name. This name may be the last
        part of the printer's URI or it may be unrelated. In
        non-US-English locales, a name may contain characters that are
        not allowed in a URI.

        """
        self.assert_running()
        return ipp.PrinterName(self.name)
    @printer_name.setter
    def printer_name(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("printer-name")

    @property
    def printer_location(self):
        """RFC 2911: 4.4.5 printer-location (text(127))

        This Printer attribute identifies the location of the
        device. This could include things like: 'in Room 123A, second
        floor of building XYZ'.
        
        """
        raise AttributeError # XXX

    @property
    def printer_info(self):
        """RFC 2911: 4.4.6 printer-info (text(127))

        This Printer attribute identifies the descriptive information
        about this Printer object. This could include things like:
        'This printer can be used for printing color transparencies
        for HR presentations', or 'Out of courtesy for others, please
        print only small (1-5 page) jobs at this printer', or even
        'This printer is going away on July 1, 1997, please find a new
        printer'.
        
        """
        raise AttributeError # XXX

    @property
    def printer_more_info(self):
        """RFC 2911: 4.4.7 printer-more-info (uri)

        This Printer attribute contains a URI used to obtain more
        information about this specific Printer object. For example,
        this could be an HTTP type URI referencing an HTML page
        accessible to a Web Browser.  The information obtained from
        this URI is intended for end user consumption. Features
        outside the scope of IPP can be accessed from this URI. The
        information is intended to be specific to this printer
        instance and site specific services (e.g. job pricing,
        services offered, end user assistance). The device
        manufacturer may initially populate this attribute.

        """
        raise AttributeError # XXX
    
    @property
    def printer_state(self):
        """RFC 2911: 4.4.11 printer-state (type1 enum)
        
        This REQUIRED Printer attribute identifies the current state
        of the device. The 'printer-state reasons' attribute augments
        the 'printer-state' attribute to give more detailed
        information about the Printer in the given printer state.

        A Printer object need only update this attribute before
        responding to an operation which requests the attribute; the
        Printer object NEED NOT update this attribute continually,
        since asynchronous event notification is not part of
        IPP/1.1. A Printer NEED NOT implement all values if they are
        not applicable to a given implementation.  The following
        standard enum values are defined:

        Value   Symbolic Name and Description
        ---------------------------------------------------------------
        '3'     'idle': Indicates that new jobs can start processing
                    without waiting.
        '4'     'processing': Indicates that jobs are processing; new 
                    jobs will wait before processing.
        '5'     'stopped': Indicates that no jobs can be processed and
                    intervention is required.

        Values of 'printer-state-reasons', such as 'spool-area-full'
        and 'stopped-partly', MAY be used to provide further
        information.
        
        """
        self.assert_running()
        return ipp.PrinterState(self.state)
    @printer_state.setter
    def printer_state(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("printer-state")

    @property
    def printer_state_reasons(self):
        """RFC 2911: 4.4.12 printer-state-reasons (1setOf type2
        keyword)

        This REQUIRED Printer attribute supplies additional detail
        about the device's state. Some of the these value definitions
        indicate conformance requirements; the rest are OPTIONAL.
        Each keyword value MAY have a suffix to indicate its level of
        severity. The three levels are: report (least severe),
        warning, and error (most severe).

        - '-report': This suffix indicates that the reason is a
          'report'.  An implementation may choose to omit some or all
          reports. Some reports specify finer granularity about the
          printer state; others serve as a precursor to a warning. A
          report MUST contain nothing that could affect the printed
          output.

        - '-warning': This suffix indicates that the reason is a
          'warning'. An implementation may choose to omit some or all
          warnings. Warnings serve as a precursor to an error. A
          warning MUST contain nothing that prevents a job from
          completing, though in some cases the output may be of lower
          quality.

        - '-error': This suffix indicates that the reason is an
          'error'.  An implementation MUST include all errors. If this
          attribute contains one or more errors, printer MUST be in
          the stopped state.

        If the implementation does not add any one of the three
        suffixes, all parties MUST assume that the reason is an
        'error'.

        If a Printer object controls more than one output device, each
        value of this attribute MAY apply to one or more of the output
        devices. An error on one output device that does not stop the
        Printer object as a whole MAY appear as a warning in the
        Printer's 'printer-state-reasons attribute'. If the
        'printer-state' for such a Printer has a value of 'stopped',
        then there MUST be an error reason among the values in the
        'printer-state-reasons' attribute.
        
        """
        self.assert_running()
        return ipp.PrinterStateReasons("none")
    @printer_state_reasons.setter
    def printer_state_reasons(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("printer-state-reasons")

    @property
    def ipp_versions_supported(self):
        """RFC 2911: 4.4.14 ipp-versions-supported (1setOf type2
        keyword)

        This REQUIRED attribute identifies the IPP protocol version(s)
        that this Printer supports, including major and minor
        versions, i.e., the version numbers for which this Printer
        implementation meets the conformance requirements. For version
        number validation, the Printer matches the (two-octet binary)
        'version-number' parameter supplied by the client in each
        request (see sections 3.1.1 and 3.1.8) with the (US-ASCII)
        keyword values of this attribute.

        The following standard keyword values are defined:
          '1.0': Meets the conformance requirement of IPP version 1.0
                as specified in RFC 2566 [RFC2566] and RFC 2565
                [RFC2565] including any extensions registered
                according to Section 6 and any extension defined in
                this version or any future version of the IPP 'Model
                and Semantics' document or the IPP 'Encoding and
                Transport' document following the rules, if any, when
                the 'version-number' parameter is '1.0'.
          '1.1': Meets the conformance requirement of IPP version 1.1
                 as specified in this document and [RFC2910] including
                 any extensions registered according to Section 6 and
                 any extension defined in any future versions of the
                 IPP 'Model and Semantics' document or the IPP
                 Encoding and Transport document following the rules,
                 if any, when the 'version-number' parameter is '1.1'.
        
        """
        self.assert_running()
        return ipp.IppVersionsSupported(*self.config['ipp-versions'])
    @ipp_versions_supported.setter
    def ipp_versions_supported(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("ipp-versions-supported")

    # XXX: We should query ourself for the supported operations
    @property
    def operations_supported(self):
        """RFC 2911: 4.4.15 operations-supported (1setOf type2 enum)

        This REQUIRED Printer attribute specifies the set of supported
        operations for this Printer object and contained Job objects.
        This attribute is encoded as any other enum attribute syntax
        according to [RFC2910] as 32-bits. However, all 32-bit enum
        values for this attribute MUST NOT exceed 0x00008FFF, since
        these same values are also passed in two octets in the
        'operation-id' parameter (see section 3.1.1) in each Protocol
        request with the two high order octets omitted in order to
        indicate the operation being performed [RFC2910].

        """
        self.assert_running()
        return ipp.OperationsSupported(ipp.OperationCodes.GET_JOBS)
    @operations_supported.setter
    def operations_supported(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("operations-supported")

    @property
    def multiple_document_jobs_supported(self):
        """RFC 2911: 4.4.16 multiple-document-jobs-supported (boolean)

        This Printer attribute indicates whether or not the Printer
        supports more than one document per job, i.e., more than one
        Send-Document or Send-Data operation with document data. If
        the Printer supports the Create-Job and Send-Document
        operations (see section 3.2.4 and 3.3.1), it MUST support this
        attribute.

        """
        self.assert_running()
        return ipp.MultipleDocumentJobsSupported(False)
    @multiple_document_jobs_supported.setter
    def multiple_document_jobs_supported(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("multiple-document-jobs-supported")

    @property
    def charset_configured(self):
        """RFC 2911: 4.4.17 charset-configured (charset)

        This REQUIRED Printer attribute identifies the charset that
        the Printer object has been configured to represent 'text' and
        'name' Printer attributes that are set by the operator, system
        administrator, or manufacturer, i.e., for 'printer-name'
        (name), 'printer-location' (text), 'printer-info' (text), and
        'printer-make- and-model' (text). Therefore, the value of the
        Printer object's 'charset-configured' attribute MUST also be
        among the values of the Printer object's 'charset-supported'
        attribute.

        """
        self.assert_running()
        return ipp.CharsetConfigured("utf-8") # XXX
    @charset_configured.setter
    def charset_configured(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("charset-configured")
        
    @property
    def charset_supported(self):
        """RFC 2911: 4.4.18 charset-supported (1setOf charset)

        This REQUIRED Printer attribute identifies the set of charsets
        that the Printer and contained Job objects support in
        attributes with attribute syntax 'text' and 'name'. At least
        the value 'utf-8' MUST be present, since IPP objects MUST
        support the UTF-8 [RFC2279] charset. If a Printer object
        supports a charset, it means that for all attributes of syntax
        'text' and 'name' the IPP object MUST (1) accept the charset
        in requests and return the charset in responses as needed.

        If more charsets than UTF-8 are supported, the IPP object MUST
        perform charset conversion between the charsets as described
        in Section 3.1.4.2.

        """
        self.assert_running()
        return ipp.CharsetSupported("utf-8") # XXX
    @charset_supported.setter
    def charset_supported(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("charset-supported")

    @property
    def natural_language_configured(self):
        """RFC 2911: 4.4.19 natural-language-configured (naturalLanguage)

        This REQUIRED Printer attribute identifies the natural
        language that the Printer object has been configured to
        represent 'text' and 'name' Printer attributes that are set by
        the operator, system administrator, or manufacturer, i.e., for
        'printer-name' (name), 'printer-location' (text),
        'printer-info' (text), and 'printer-make- and-model'
        (text). When returning these Printer attributes, the Printer
        object MAY return them in the configured natural language
        specified by this attribute, instead of the natural language
        requested by the client in the 'attributes-natural-language'
        operation attribute. See Section 3.1.4.1 for the specification
        of the OPTIONAL multiple natural language support. Therefore,
        the value of the Printer object's
        'natural-language-configured' attribute MUST also be among the
        values of the Printer object's 'generated-natural-
        language-supported' attribute.

        """
        self.assert_running()
        return ipp.NaturalLanguageConfigured("en-us")
    @natural_language_configured.setter
    def natural_language_configured(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("natural-language-configured")

    @property
    def generated_natural_language_supported(self):
        """RFC 2911: 4.4.20 generated-natural-language-supported
        (1setOf naturalLanguage)

        This REQUIRED Printer attribute identifies the natural
        language(s) that the Printer object and contained Job objects
        support in attributes with attribute syntax 'text' and
        'name'. The natural language(s) supported depends on
        implementation and/or configuration.  Unlike charsets, IPP
        objects MUST accept requests with any natural language or any
        Natural Language Override whether the natural language is
        supported or not.

        If a Printer object supports a natural language, it means that
        for any of the attributes for which the Printer or Job object
        generates messages, i.e., for the 'job-state-message' and
        'printer-state- message' attributes and Operation Messages
        (see Section 3.1.5) in operation responses, the Printer and
        Job objects MUST be able to generate messages in any of the
        Printer's supported natural languages. See section 3.1.4 for
        the definition of 'text' and 'name' attributes in operation
        requests and responses.
        
        Note: A Printer object that supports multiple natural
        languages, often has separate catalogs of messages, one for
        each natural language supported.

        """
        self.assert_running()
        return ipp.GeneratedNaturalLanguageSupported("en-us")
    @generated_natural_language_supported.setter
    def generated_natural_language_supported(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("generated-natural-language-supported")

    @property
    def document_format_default(self):
        """RFC 2911: 4.4.21 document-format-default (mimeMediaType)

        This REQUIRED Printer attribute identifies the document format
        that the Printer object has been configured to assume if the
        client does not supply a 'document-format' operation attribute
        in any of the operation requests that supply document
        data. The standard values for this attribute are Internet
        Media types (sometimes called MIME types). For further details
        see the description of the 'mimeMediaType' attribute syntax in
        Section 4.1.9.

        """
        self.assert_running()
        return ipp.DocumentFormatDefault("application/octet-stream")
    @document_format_default.setter
    def document_format_default(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("document-format-default")

    @property
    def document_format_supported(self):
        """RFC 2911: 4.4.22 document-format-supported (1setOf mimeMediaType)

        This REQUIRED Printer attribute identifies the set of document
        formats that the Printer object and contained Job objects can
        support. For further details see the description of the
        'mimeMediaType' attribute syntax in Section 4.1.9.

        """
        self.assert_running()
        return ipp.DocumentFormatSupported("application/octet-stream", "audio/mp3")
    @document_format_supported.setter
    def document_format_supported(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("document-format-supported")

    @property
    def printer_is_accepting_jobs(self):
        """RFC 2911: 4.4.23 printer-is-accepting-jobs (boolean)

        This REQUIRED Printer attribute indicates whether the printer
        is currently able to accept jobs, i.e., is accepting
        Print-Job, Print- URI, and Create-Job requests. If the value
        is 'true', the printer is accepting jobs. If the value is
        'false', the Printer object is currently rejecting any jobs
        submitted to it. In this case, the Printer object returns the
        'server-error-not-accepting-jobs' status code.

        This value is independent of the 'printer-state' and
        'printer-state- reasons' attributes because its value does not
        affect the current job; rather it affects future jobs. This
        attribute, when 'false', causes the Printer to reject jobs
        even when the 'printer-state' is 'idle' or, when 'true',
        causes the Printer object to accepts jobs even when the
        'printer-state' is 'stopped'.

        """
        self.assert_running()
        return ipp.PrinterIsAcceptingJobs(True) # XXX
    @printer_is_accepting_jobs.setter
    def printer_is_accepting_jobs(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("printer-is-accepting-jobs")

    @property
    def queued_job_count(self):
        """RFC 2911: 4.4.24 queued-job-count (integer(0:MAX))

        This REQUIRED Printer attribute contains a count of the number
        of jobs that are either 'pending', 'processing',
        'pending-held', or 'processing-stopped' and is set by the
        Printer object.

        """
        self.assert_running()
        return ipp.QueuedJobCount(len(self.active_jobs))
    @queued_job_count.setter
    def queued_job_count(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("queued-job-count")

    @property
    def pdl_override_supported(self):
        """RFC 2911: 4.4.28 pdl-override-supported (type2 keyword)

        This REQUIRED Printer attribute expresses the ability for a
        particular Printer implementation to either attempt to
        override document data instructions with IPP attributes or
        not.

        This attribute takes on the following keyword values:

          - 'attempted': This value indicates that the Printer object
            attempts to make the IPP attribute values take precedence
            over embedded instructions in the document data, however
            there is no guarantee.

          - 'not-attempted': This value indicates that the Printer
            object makes no attempt to make the IPP attribute values
            take precedence over embedded instructions in the document
            data.

        Section 15 contains a full description of how this attribute
        interacts with and affects other IPP attributes, especially
        the 'ipp-attribute-fidelity' attribute.

        """
        self.assert_running()
        return ipp.PdlOverrideSupported("not-attempted")
    @pdl_override_supported.setter
    def pdl_override_supported(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("pdl-override-supported")

    @property
    def printer_up_time(self):
        """RFC 2911: 4.4.29 printer-up-time (integer(1:MAX))

        This REQUIRED Printer attribute indicates the amount of time
        (in seconds) that this Printer instance has been up and
        running. The value is a monotonically increasing value
        starting from 1 when the Printer object is started-up
        (initialized, booted, etc.). This value is used to populate
        the Event Time Job Description Job attributes
        'time-at-creation', 'time-at-processing', and
        'time-at-completed' (see section 4.3.14).

        If the Printer object goes down at some value 'n', and comes
        back up, the implementation MAY:

            1. Know how long it has been down, and resume at some
               value greater than 'n', or
            2. Restart from 1.

        In other words, if the device or devices that the Printer
        object is representing are restarted or power cycled, the
        Printer object MAY continue counting this value or MAY reset
        this value to 1 depending on implementation. However, if the
        Printer object software ceases running, and restarts without
        knowing the last value for 'printer- up-time', the
        implementation MUST reset this value to 1. If this value is
        reset and the Printer has persistent jobs, the Printer MUST
        reset the 'time-at-xxx(integer) Event Time Job Description
        attributes according to Section 4.3.14. An implementation MAY
        use both implementation alternatives, depending on warm versus
        cold start, respectively.

        """
        self.assert_running()
        return ipp.PrinterUpTime(int(time.time()) - self.time_created)
    @printer_up_time.setter
    def printer_up_time(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("printer-up-time")

    @property
    def printer_current_time(self):
        """RFC 2911: 4.4.30 printer-current-time (dateTime)
        
        This Printer attribute indicates the current date and
        time. This value is used to populate the Event Time Job
        Description attributes: 'date-time-at-creation',
        'date-time-at-processing', and 'date-time- at-completed' (see
        Section 4.3.14).

        The date and time is obtained on a 'best efforts basis' and
        does not have to be that precise in order to work in
        practice. A Printer implementation sets the value of this
        attribute by obtaining the date and time via some
        implementation-dependent means, such as getting the value from
        a network time server, initialization at time of manufacture,
        or setting by an administrator. See [IPP-IIG] for examples. If
        an implementation supports this attribute and the
        implementation knows that it has not yet been set, then the
        implementation MUST return the value of this attribute using
        the out-of-band 'no-value' meaning not configured. See the
        beginning of section 4.1.

        The time zone of this attribute NEED NOT be the time zone used
        by people located near the Printer object or device. The
        client MUST NOT expect that the time zone of any received
        'dateTime' value to be in the time zone of the client or in
        the time zone of the people located near the printer.

        The client SHOULD display any dateTime attributes to the user
        in client local time by converting the 'dateTime' value
        returned by the server to the time zone of the client, rather
        than using the time zone returned by the Printer in attributes
        that use the 'dateTime' attribute syntax.

        """
        raise AttributeError # XXX

    @property
    def multiple_operation_time_out(self):
        """RFC 2911: 4.4.31 multiple-operation-time-out
        (integer(1:MAX))

        This Printer attributes identifies the minimum time (in
        seconds) that the Printer object waits for additional
        Send-Document or Send-URI operations to follow a still-open
        Job object before taking any recovery actions, such as the
        ones indicated in section 3.3.1. If the Printer object
        supports the Create-Job and Send-Document operations (see
        section 3.2.4 and 3.3.1), it MUST support this attribute.

        It is RECOMMENDED that vendors supply a value for this
        attribute that is between 60 and 240 seconds. An
        implementation MAY allow a system administrator to set this
        attribute (by means outside this IPP/1.1 document). If so, the
        system administrator MAY be able to set values outside this
        range.

        """
        self.assert_running()
        return ipp.MultipleOperationTimeOut(240)
    @multiple_operation_time_out.setter
    def multiple_operation_time_out(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("multiple-operation-time-out")

    @property
    def compression_supported(self):
        """RFC 2911: 4.4.32 compression-supported (1setOf type3
        keyword)

        This REQUIRED Printer attribute identifies the set of
        supported compression algorithms for document
        data. Compression only applies to the document data;
        compression does not apply to the encoding of the IPP
        operation itself. The supported values are used to validate
        the client supplied 'compression' operation attributes in
        Print-Job, Send-Document, and Send-URI requests.

        Standard keyword values are :
            'none': no compression is used.
            'deflate': ZIP public domain inflate/deflate) compression
                technology in RFC 1951 [RFC1951]
            'gzip' GNU zip compression technology described in RFC
                1952 [RFC1952].
            'compress': UNIX compression technology in RFC 1977 [RFC1977]

        """
        self.assert_running()
        return ipp.CompressionSupported("none")
    @compression_supported.setter
    def compression_supported(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("compression-supported")

    ######################################################################
    ###                      Job IPP Attributes                        ###
    ######################################################################

    def job_uri(self, job_id):
        """RFC 2911: 4.3.1 job-uri (uri)

        This REQUIRED attribute contains the URI for the job. The
        Printer object, on receipt of a new job, generates a URI which
        identifies the new Job. The Printer object returns the value
        of the 'job-uri' attribute as part of the response to a create
        request. The precise format of a Job URI is implementation
        dependent. If the Printer object supports more than one URI
        and there is some relationship between the newly formed Job
        URI and the Printer object's URI, the Printer object uses the
        Printer URI supplied by the client in the create request. For
        example, if the create request comes in over a secure channel,
        the new Job URI MUST use the same secure channel.  This can be
        guaranteed because the Printer object is responsible for
        generating the Job URI and the Printer object is aware of its
        security configuration and policy as well as the Printer URI
        used in the create request.

        For a description of this attribute and its relationship to
        'job-id' and 'job-printer-uri' attribute, see the discussion
        in section 2.4 on 'Object Identity'.

        """
        raise AttributeError # XXX

    def job_id(self, job_id):
        """RFC 2911: 4.3.2 job-id (integer(1:MAX))

        This REQUIRED attribute contains the ID of the job. The
        Printer, on receipt of a new job, generates an ID which
        identifies the new Job on that Printer. The Printer returns
        the value of the 'job-id' attribute as part of the response to
        a create request. The 0 value is not included to allow for
        compatibility with SNMP index values which also cannot be 0.

        For a description of this attribute and its relationship to
        'job-uri' and 'job-printer-uri' attribute, see the discussion
        in section 2.4 on 'Object Identity'.

        """
        self.assert_running()
        job = self.get_job(job_id)
        return ipp.JobId(job.id)

    def job_printer_uri(self, job_id):
        """RFC 2911: 4.3.3 job-printer-uri (uri)

        This REQUIRED attribute identifies the Printer object that
        created this Job object. When a Printer object creates a Job
        object, it populates this attribute with the Printer object
        URI that was used in the create request. This attribute
        permits a client to identify the Printer object that created
        this Job object when only the Job object's URI is available to
        the client. The client queries the creating Printer object to
        determine which languages, charsets, operations, are supported
        for this Job.

        For a description of this attribute and its relationship to
        'job-uri' and 'job-id' attribute, see the discussion in
        section 2.4 on 'Object Identity'.

        """
        self.assert_running()
        job = self.get_job(job_id)
        return ipp.JobPrinterUri(self.uri)

    def job_name(self, job_id):
        """RFC 2911: 4.3.5 job-name (name(MAX))

        This REQUIRED attribute is the name of the job. It is a name
        that is more user friendly than the 'job-uri' attribute
        value. It does not need to be unique between Jobs. The Job's
        'job-name' attribute is set to the value supplied by the
        client in the 'job-name' operation attribute in the create
        request (see Section 3.2.1.1).

        If, however, the 'job-name' operation attribute is not
        supplied by the client in the create request, the Printer
        object, on creation of the Job, MUST generate a name. The
        printer SHOULD generate the value of the Job's 'job-name'
        attribute from the first of the following sources that
        produces a value: 1) the 'document-name' operation attribute
        of the first (or only) document, 2) the 'document-URI'
        attribute of the first (or only) document, or 3) any other
        piece of Job specific and/or Document Content information.
        
        """
        self.assert_running()
        job = self.get_job(job_id)
        return ipp.JobName(job.name)

    def job_originating_user_name(self, job_id):
        """RFC 2911: 4.3.6 job-originating-user-name (name(MAX))

        This REQUIRED attribute contains the name of the end user that
        submitted the print job. The Printer object sets this
        attribute to the most authenticated printable name that it can
        obtain from the authentication service over which the IPP
        operation was received.  Only if such is not available, does
        the Printer object use the value supplied by the client in the
        'requesting-user-name' operation attribute of the create
        operation (see Sections 4.4.2, 4.4.3, and 8).

        Note: The Printer object needs to keep an internal originating
        user id of some form, typically as a credential of a
        principal, with the Job object. Since such an internal
        attribute is implementation- dependent and not of interest to
        clients, it is not specified as a Job Description
        attribute. This originating user id is used for authorization
        checks (if any) on all subsequent operations.

        """
        self.assert_running()
        job = self.get_job(job_id)
        return ipp.JobOriginatingUserName(job.creator)

    def job_state(self, job_id):
        """RFC 2911: 4.3.7 job-state (type1 enum)

        This REQUIRED attribute identifies the current state of the
        job.  Even though the IPP protocol defines seven values for
        job states (plus the out-of-band 'unknown' value - see Section
        4.1), implementations only need to support those states which
        are appropriate for the particular implementation. In other
        words, a Printer supports only those job states implemented by
        the output device and available to the Printer object
        implementation.  Standard enum values are:

            '3' 'pending': The job is a candidate to start processing,
                but is not yet processing.

            '4' 'pending-held': The job is not a candidate for
                processing for any number of reasons but will return
                to the 'pending' state as soon as the reasons are no
                longer present. The job's 'job-state-reason' attribute
                MUST indicate why the job is no longer a candidate for
                processing.

            '5' 'processing': One or more of:

                1. the job is using, or is attempting to use, one or
                   more purely software processes that are analyzing,
                   creating, or interpreting a PDL, etc.,
                2. the job is using, or is attempting to use, one or
                   more hardware devices that are interpreting a PDL,
                   making marks on a medium, and/or performing
                   finishing, such as stapling, etc.,
                3. the Printer object has made the job ready for
                   printing, but the output device is not yet printing
                   it, either because the job hasn't reached the
                   output device or because the job is queued in the
                   output device or some other spooler, awaiting the
                   output device to print it.

                When the job is in the 'processing' state, the entire
                job state includes the detailed status represented in
                the Printer object's 'printer-state', 'printer-state-
                reasons', and 'printer-state-message' attributes.

                Implementations MAY, though they NEED NOT, include
                additional values in the job's 'job-state-reasons'
                attribute to indicate the progress of the job, such as
                adding the 'job-printing' value to indicate when the
                output device is actually making marks on paper and/or
                the 'processing-to-stop-point' value to indicate that
                the IPP object is in the process of canceling or
                aborting the job. Most implementations won't bother
                with this nuance.

            '6' 'processing-stopped': The job has stopped while
                processing for any number of reasons and will return
                to the 'processing' state as soon as the reasons are
                no longer present.

                The job's 'job-state-reason' attribute MAY indicate
                why the job has stopped processing. For example, if
                the output device is stopped, the 'printer-stopped'
                value MAY be included in the job's 'job-state-reasons'
                attribute.

                Note: When an output device is stopped, the device
                usually indicates its condition in human readable form
                locally at the device. A client can obtain more
                complete device status remotely by querying the
                Printer object's 'printer-state',
                'printer-state-reasons' and 'printer- state-message'
                attributes.

            '7' 'canceled': The job has been canceled by a Cancel-Job
                operation and the Printer object has completed
                canceling the job and all job status attributes have
                reached their final values for the job. While the
                Printer object is canceling the job, the job remains
                in its current state, but the job's
                'job-state-reasons' attribute SHOULD contain the
                'processing-to-stop-point' value and one of the
                'canceled-by-user', 'canceled-by-operator', or
                'canceled-at-device' value. When the job moves to the
                'canceled' state, the 'processing-to-stop-point'
                value, if present, MUST be removed, but the
                'canceled-by-xxx', if present, MUST remain.

            '8' 'aborted': The job has been aborted by the system,
                usually while the job was in the 'processing' or
                'processing- stopped' state and the Printer has
                completed aborting the job and all job status
                attributes have reached their final values for the
                job. While the Printer object is aborting the job, the
                job remains in its current state, but the job's
                'job-state-reasons' attribute SHOULD contain the
                'processing-to-stop-point' and 'aborted-by- system'
                values. When the job moves to the 'aborted' state, the
                'processing-to-stop-point' value, if present, MUST be
                removed, but the 'aborted-by-system' value, if
                present, MUST remain.

            '9' 'completed': The job has completed successfully or
                with warnings or errors after processing and all of
                the job media sheets have been successfully stacked in
                the appropriate output bin(s) and all job status
                attributes have reached their final values for the
                job. The job's 'job-state-reasons' attribute SHOULD
                contain one of: 'completed-successfully',
                'completed-with-warnings', or 'completed-with-errors'
                values.

        The final value for this attribute MUST be one of:
        'completed', 'canceled', or 'aborted' before the Printer
        removes the job altogether. The length of time that jobs
        remain in the 'canceled', 'aborted', and 'completed' states
        depends on implementation. See section 4.3.7.2.

        The following figure shows the normal job state transitions.
        
                                                           +----> canceled
                                                          /
            +----> pending --------> processing ---------+------> completed
            |         ^                   ^               \
        --->+         |                   |                +----> aborted
            |         v                   v               /
            +----> pending-held    processing-stopped ---+

        Normally a job progresses from left to right. Other state
        transitions are unlikely, but are not forbidden. Not shown are
        the transitions to the 'canceled' state from the 'pending',
        'pending- held', and 'processing-stopped' states.

        Jobs reach one of the three terminal states: 'completed',
        'canceled', or 'aborted', after the jobs have completed all
        activity, including stacking output media, after the jobs have
        completed all activity, and all job status attributes have
        reached their final values for the job.

        """
        self.assert_running()
        job = self.get_job(job_id)
        return ipp.JobState(job.state)

    def job_k_octets(self, job_id):
        """RFC 2911: 4.3.17.1 job-k-octets (integer(0:MAX))

        This attribute specifies the total size of the document(s) in
        K octets, i.e., in units of 1024 octets requested to be
        processed in the job. The value MUST be rounded up, so that a
        job between 1 and 1024 octets MUST be indicated as being 1,
        1025 to 2048 MUST be 2, etc.

        This value MUST NOT include the multiplicative factors
        contributed by the number of copies specified by the 'copies'
        attribute, independent of whether the device can process
        multiple copies without making multiple passes over the job or
        document data and independent of whether the output is
        collated or not. Thus the value is independent of the
        implementation and indicates the size of the document(s)
        measured in K octets independent of the number of copies.

        This value MUST also not include the multiplicative factor due
        to a copies instruction embedded in the document data. If the
        document data actually includes replications of the document
        data, this value will include such replication. In other
        words, this value is always the size of the source document
        data, rather than a measure of the hardcopy output to be
        produced.

        """
        self.assert_running()
        job = self.get_job(job_id)
        return ipp.JobKOctets(int(math.ceil(job.size / 1024.)))

    def job_k_octets_completed(self, job_id):
        """RFC 2911: 4.3.18.1 job-k-octets-processed (integer(0:MAX))

        This attribute specifies the total number of octets processed
        in K octets, i.e., in units of 1024 octets so far. The value
        MUST be rounded up, so that a job between 1 and 1024 octets
        inclusive MUST be indicated as being 1, 1025 to 2048 inclusive
        MUST be 2, etc.  For implementations where multiple copies are
        produced by the interpreter with only a single pass over the
        data, the final value MUST be equal to the value of the
        'job-k-octets' attribute. For implementations where multiple
        copies are produced by the interpreter by processing the data
        for each copy, the final value MUST be a multiple of the value
        of the 'job-k-octets' attribute.

        """
        raise AttributeError # XXX

    def attributes_charset(self, job_id):
        """RFC 2911: 4.3.19 attributes-charset (charset)

        This REQUIRED attribute is populated using the value in the
        client supplied 'attributes-charset' attribute in the create
        request. It identifies the charset (coded character set and
        encoding method) used by any Job attributes with attribute
        syntax 'text' and 'name' that were supplied by the client in
        the create request. See Section 3.1.4 for a complete
        description of the 'attributes-charset' operation attribute.

        This attribute does not indicate the charset in which the
        'text' and 'name' values are stored internally in the Job
        object. The internal charset is implementation-defined. The
        IPP object MUST convert from whatever the internal charset is
        to that being requested in an operation as specified in
        Section 3.1.4.

        """
        raise AttributeError # XXX

    def attributes_natural_language(self, job_id):
        """RFC 2911: 4.3.20 attributes-natural-language
        (naturalLanguage)

        This REQUIRED attribute is populated using the value in the
        client supplied 'attributes-natural-language' attribute in the
        create request. It identifies the natural language used for
        any Job attributes with attribute syntax 'text' and 'name'
        that were supplied by the client in the create request. See
        Section 3.1.4 for a complete description of the
        'attributes-natural-language' operation attribute. See
        Sections 4.1.1.2 and 4.1.2.2 for how a Natural Language
        Override may be supplied explicitly for each 'text' and 'name'
        attribute value that differs from the value identified by the
        'attributes-natural-language' attribute.

        """
        raise AttributeError # XXX

    ######################################################################
    ###                        IPP Operations                          ###
    ######################################################################

    @sync
    def print_job(self, document, document_name=None, document_format=None,
                  document_natural_language=None, requesting_user_name=None,
                  compression=None, job_name=None, job_k_octets=None):
        """RFC 2911: 3.2.1 Print-Job Operation
        
        This REQUIRED operation allows a client to submit a print job
        with only one document and supply the document data (rather
        than just a reference to the data). See Section 15 for the
        suggested steps for processing create operations and their
        Operation and Job Template attributes.

        Parameters
        ----------
        document (file)
            an open file handler to the document
        document_name (string)
            the name of the document
        document_format (string)
            the encoding/format of the document
        document_natural_language (string)
            if the document is a text file, what language it is in
        requesting_user_name (string)
            the user name of the job owner
        compression (string)
            the form of compression used on the file
        job_name (string)
            the name that the job should be called
        job_k_octets (int)
            the size of the job in bytes

        """
        
        self.assert_running()

        # create the job
        job_id = self.create_job(
            requesting_user_name=requesting_user_name,
            job_name=job_name,
            job_k_octets=job_k_octets)
        
        # send the document
        self.send_document(
            job_id,
            document,
            document_name=document_name,
            document_format=document_format,
            document_natural_language=document_natural_language,
            requesting_user_name=requesting_user_name,
            compression=compression,
            last_document=False)

        return job_id

    @sync
    def validate_job(self, document_name=None, document_format=None,
                     document_natural_language=None, requesting_user_name=None,
                     compression=None, job_name=None, job_k_octets=None):
        """RFC 2911: 3.2.3 Validate-Job Operation

        This REQUIRED operation is similar to the Print-Job operation
        (section 3.2.1) except that a client supplies no document data
        and the Printer allocates no resources (i.e., it does not
        create a new Job object).  This operation is used only to
        verify capabilities of a printer object against whatever
        attributes are supplied by the client in the Validate-Job
        request.  By using the Validate-Job operation a client can
        validate that an identical Print-Job operation (with the
        document data) would be accepted. The Validate-Job operation
        also performs the same security negotiation as the Print-Job
        operation (see section 8), so that a client can check that the
        client and Printer object security requirements can be met
        before performing a Print-Job operation.

        The Validate-Job operation does not accept a 'document-uri'
        attribute in order to allow a client to check that the same
        Print-URI operation will be accepted, since the client doesn't
        send the data with the Print-URI operation.  The client SHOULD
        just issue the Print-URI request.

        Parameters
        ----------
        document (file)
            an open file handler to the document
        document_name (string)
            the name of the document
        document_format (string)
            the encoding/format of the document
        document_natural_language (string)
            if the document is a text file, what language it is in
        requesting_user_name (string)
            the user name of the job owner
        compression (string)
            the form of compression used on the file
        job_name (string)
            the name that the job should be called
        job_k_octets (int)
            the size of the job in bytes

        """
        
        self.assert_running()

        job_id = self._next_job_id
        job = GutenbachJob(
            job_id,
            creator=requesting_user_name,
            name=job_name)
        job.spool(tempfile.TemporaryFile())
        job.abort()
        del job

    @sync
    def get_jobs(self, requesting_user_name=None, which_jobs=None,
                 requested_attributes=None):
        """RFC 2911: 3.2.6 Get-Jobs Operation
        
        This REQUIRED operation allows a client to retrieve the list
        of Job objects belonging to the target Printer object. The
        client may also supply a list of Job attribute names and/or
        attribute group names. A group of Job object attributes will
        be returned for each Job object that is returned.

        This operation is similar to the Get-Job-Attributes operation,
        except that this Get-Jobs operation returns attributes from
        possibly more than one object.

        Parameters
        ----------
        requesting_user_name (string)
            the user name of the job owner, used as a filter
        which_jobs (string)
            a filter for the types of jobs to return:
              * 'completed' -- only jobs that have finished
              * 'not-completed' -- processing or pending jobs
            this defaults to 'not-completed'
        requested_attributes (list)
            the job attributes to return

        """
        
        self.assert_running()

        # Filter by the which-jobs attribute
        if which_jobs is None:
            which_jobs = "not-completed"

        if which_jobs == "completed":
            jobs = [self.jobs[job_id] for job_id in self.finished_jobs]
        elif which_jobs == "not-completed":
            jobs = [self.jobs[job_id] for job_id in self.active_jobs]
        else:
            raise ipp.errors.ClientErrorAttributes(
                which_jobs, ipp.WhichJobs(which_jobs))

        # Filter by username
        if requesting_user_name is None:
            user_jobs = jobs
        else:
            user_jobs = [job for job in jobs if job.creator == requesting_user_name]

        # Get the attributes of each job
        job_attrs = [self.get_job_attributes(
            job.id, requested_attributes=requested_attributes) for job in user_jobs]
        
        return job_attrs

    @sync
    def print_uri(self):
        """RFC 2911: 3.2.2 Print-URI Operation

        This OPTIONAL operation is identical to the Print-Job
        operation (section 3.2.1) except that a client supplies a URI
        reference to the document data using the 'document-uri' (uri)
        operation attribute (in Group 1) rather than including the
        document data itself.  Before returning the response, the
        Printer MUST validate that the Printer supports the retrieval
        method (e.g., http, ftp, etc.) implied by the URI, and MUST
        check for valid URI syntax.  If the client-supplied URI scheme
        is not supported, i.e. the value is not in the Printer
        object's 'referenced-uri-scheme-supported' attribute, the
        Printer object MUST reject the request and return the
        'client-error-uri- scheme-not-supported' status code.
                                                                              
        If the Printer object supports this operation, it MUST support
        the 'reference-uri-schemes-supported' Printer attribute (see
        section 4.4.27).

        It is up to the IPP object to interpret the URI and
        subsequently 'pull' the document from the source referenced by
        the URI string.

        """
        
        self.assert_running()
        # XXX: todo

    @sync
    def create_job(self, requesting_user_name=None,
                   job_name=None, job_k_octets=None):
        """RFC 2911: 3.2.4 Create-Job Operation

        This OPTIONAL operation is similar to the Print-Job operation
        (section 3.2.1) except that in the Create-Job request, a
        client does not supply document data or any reference to
        document data. Also, the client does not supply any of the
        'document-name', 'document- format', 'compression', or
        'document-natural-language' operation attributes. This
        operation is followed by one or more Send-Document or Send-URI
        operations. In each of those operation requests, the client
        OPTIONALLY supplies the 'document-name', 'document-format',
        and 'document-natural-language' attributes for each document
        in the multi-document Job object.

        Parameters
        ----------
        requesting_user_name (string)
            the user name of the job owner
        job_name (string)
            the name that the job should be called
        job_k_octets (int)
            the size of the job in bytes

        """
        
        self.assert_running()

        job_id = self._next_job_id
        self._next_job_id += 1
        
        job = GutenbachJob(
            job_id,
            creator=requesting_user_name,
            name=job_name)

        self.jobs[job_id] = job
        return job_id

    @sync
    def pause_printer(self):
        """RFC 2911: 3.2.7 Pause-Printer Operation

        This OPTIONAL operation allows a client to stop the Printer
        object from scheduling jobs on all its devices.  Depending on
        implementation, the Pause-Printer operation MAY also stop the
        Printer from processing the current job or jobs.  Any job that
        is currently being printed is either stopped as soon as the
        implementation permits or is completed, depending on
        implementation.  The Printer object MUST still accept create
        operations to create new jobs, but MUST prevent any jobs from
        entering the 'processing' state.

        If the Pause-Printer operation is supported, then the
        Resume-Printer operation MUST be supported, and vice-versa.

        The IPP Printer MUST accept the request in any state and
        transition the Printer to the indicated new 'printer-state'
        before returning as follows:

        Current       New         Reasons             Reponse
        --------------------------------------------------------------
        'idle'       'stopped'    'paused'            'successful-ok'
        'processing' 'processing' 'moving-to-paused'  'successful-ok'
        'processing' 'stopped'    'paused'            'successful-ok'
        'stopped'    'stopped'    'paused'            'successful-ok'

        """
        
        self.assert_running()
        if not self.paused:
            if self.current_job is not None and self.current_job.is_playing:
                self.current_job.pause()
            self.paused = True
            logger.info("%s paused", str(self))

    @sync
    def resume_printer(self):
        """RFC 2911: 3.2.8 Resume-Printer Operation

        This operation allows a client to resume the Printer object
        scheduling jobs on all its devices.  The Printer object MUST
        remove the 'paused' and 'moving-to-paused' values from the
        Printer object's 'printer-state-reasons' attribute, if
        present.  If there are no other reasons to keep a device
        paused (such as media-jam), the IPP Printer is free to
        transition itself to the 'processing' or 'idle' states,
        depending on whether there are jobs to be processed or not,
        respectively, and the device(s) resume processing jobs.

        If the Pause-Printer operation is supported, then the
        Resume-Printer operation MUST be supported, and vice-versa.

        The IPP Printer removes the 'printer-stopped' value from any
        job's 'job-state-reasons' attributes contained in that
        Printer.

        The IPP Printer MUST accept the request in any state,
        transition the Printer object to the indicated new state as
        follows:

        Current       New           Response
        ---------------------------------------------
        'idle'       'idle'         'successful-ok'
        'processing' 'processing'   'successful-ok'
        'stopped'    'processing'   'successful-ok'
        'stopped'    'idle'         'successful-ok'

        """
        
        self.assert_running()
        if self.paused:
            if self.current_job is not None:
                self.current_job.resume()
            self.paused = False
            logger.info("%s unpaused", str(self))

    @sync
    def get_printer_attributes(self, requested_attributes=None):
        """RFC 2911: 3.2.5 Get-Printer-Attributes Operation

        This REQUIRED operation allows a client to request the values
        of the attributes of a Printer object.
        
        In the request, the client supplies the set of Printer
        attribute names and/or attribute group names in which the
        requester is interested. In the response, the Printer object
        returns a corresponding attribute set with the appropriate
        attribute values filled in.

        Parameters
        ----------
        requested_attributes (list)
            the attributes to return

        """
        
        self.assert_running()
        if requested_attributes is None:
            requested = self.printer_attributes
        else:
            requested = [a for a in self.printer_attributes \
                         if a in requested_attributes]

        _attributes = [attr.replace("-", "_") for attr in requested]
        attributes = [getattr(self, attr) for attr in _attributes]
        return attributes

    @sync
    def set_printer_attributes(self, attributes):
        self.assert_running()
        for attr in attributes:
            try:
                setattr(self, attr, attributes[attr])
            except AttributeError:
                raise ipp.errors.ClientErrorAttributes

    @sync
    def cancel_job(self, job_id, requesting_user_name=None):
        """RFC 2911: 3.3.3 Cancel-Job Operation

        This REQUIRED operation allows a client to cancel a Print Job
        from the time the job is created up to the time it is
        completed, canceled, or aborted. Since a Job might already be
        printing by the time a Cancel-Job is received, some media
        sheet pages might be printed before the job is actually
        terminated.

        The IPP object MUST accept or reject the request based on the
        job's current state and transition the job to the indicated
        new state as follows:

        Current State       New State           Response
        -----------------------------------------------------------------
        pending             canceled            successful-ok
        pending-held        canceled            successful-ok
        processing          canceled            successful-ok
        processing          processing          successful-ok               See Rule 1
        processing          processing          client-error-not-possible   See Rule 2
        processing-stopped  canceled            successful-ok
        processing-stopped  processing-stopped  successful-ok               See Rule 1
        processing-stopped  processing-stopped  client-error-not-possible   See Rule 2
        completed           completed           client-error-not-possible
        canceled            canceled            client-error-not-possible
        aborted             aborted             client-error-not-possible

        Rule 1: If the implementation requires some measurable time to
        cancel the job in the 'processing' or 'processing-stopped' job
        states, the IPP object MUST add the 'processing-to-stop-point'
        value to the job's 'job-state-reasons' attribute and then
        transition the job to the 'canceled' state when the processing
        ceases (see section 4.3.8).

        Rule 2: If the Job object already has the
        'processing-to-stop-point' value in its 'job-state-reasons'
        attribute, then the Printer object MUST reject a Cancel-Job
        operation.

        Parameters
        ----------
        job_id (integer)
            the id of the job to cancel
        requesting_user_name (string)
            the name of the job's owner

        """

        self.assert_running()
        job = self.get_job(job_id)
        try:
            job.cancel()
        except InvalidJobStateException:
            # XXX
            raise

    @sync
    def send_document(self, job_id, document, document_name=None,
                      document_format=None, document_natural_language=None,
                      requesting_user_name=None, compression=None,
                      last_document=None):
        """RFC 2911: 3.3.1 Send-Document Operation
        
        This OPTIONAL operation allows a client to create a
        multi-document Job object that is initially 'empty' (contains
        no documents). In the Create-Job response, the Printer object
        returns the Job object's URI (the 'job-uri' attribute) and the
        Job object's 32-bit identifier (the 'job-id' attribute). For
        each new document that the client desires to add, the client
        uses a Send-Document operation. Each Send- Document Request
        contains the entire stream of document data for one document.

        If the Printer supports this operation but does not support
        multiple documents per job, the Printer MUST reject subsequent
        Send-Document operations supplied with data and return the
        'server-error-multiple- document-jobs-not-supported'. However,
        the Printer MUST accept the first document with a 'true' or
        'false' value for the 'last-document' operation attribute (see
        below), so that clients MAY always submit one document jobs
        with a 'false' value for 'last-document' in the first
        Send-Document and a 'true' for 'last-document' in the second
        Send-Document (with no data).
        
        Since the Create-Job and the send operations (Send-Document or
        Send- URI operations) that follow could occur over an
        arbitrarily long period of time for a particular job, a client
        MUST send another send operation within an IPP Printer defined
        minimum time interval after the receipt of the previous
        request for the job. If a Printer object supports the
        Create-Job and Send-Document operations, the Printer object
        MUST support the 'multiple-operation-time-out' attribute (see
        section 4.4.31). This attribute indicates the minimum number
        of seconds the Printer object will wait for the next send
        operation before taking some recovery action.

        An IPP object MUST recover from an errant client that does not
        supply a send operation, sometime after the minimum time
        interval specified by the Printer object's
        'multiple-operation-time-out' attribute.

        Parameters
        ----------
        job_id (integer)
            the id of the job to send the document
        document (file)
            an open file handler to the document
        document_name (string)
            the name of the document
        document_format (string)
            the encoding/format of the document
        document_natural_language (string)
            if the document is a text file, what language it is in
        requesting_user_name (string)
            the user name of the job owner
        compression (string)
            the form of compression used on the file
        last_document (boolean)
            whether or not this is the last document in this job

        """
        
        self.assert_running()
        job = self.get_job(job_id)
        job.spool(document)
        if 'dryrun' in self.config and self.config['dryrun']:
            job.player._dryrun = True
        self.pending_jobs.append(job_id)
        
    @sync
    def send_uri(self, job_id, document_uri, document_name=None,
                 document_format=None, document_natural_language=None,
                 requesting_user_name=None, compression=None,
                 last_document=None):
        """RFC 2911: 3.2.2 Send URI

        This OPTIONAL operation is identical to the Send-Document
        operation (see section 3.3.1) except that a client MUST supply
        a URI reference ('document-uri' operation attribute) rather
        than the document data itself.  If a Printer object supports
        this operation, clients can use both Send-URI or Send-Document
        operations to add new documents to an existing multi-document
        Job object.  However, if a client needs to indicate that the
        previous Send-URI or Send-Document was the last document, the
        client MUST use the Send-Document operation with no document
        data and the 'last-document' flag set to 'true' (rather than
        using a Send-URI operation with no 'document-uri' operation
        attribute).

        If a Printer object supports this operation, it MUST also
        support the Print-URI operation (see section 3.2.2).

        The Printer object MUST validate the syntax and URI scheme of
        the supplied URI before returning a response, just as in the
        Print-URI operation.  The IPP Printer MAY validate the
        accessibility of the document as part of the operation or
        subsequently (see section 3.2.2).

        Parameters
        ----------
        job_id (integer)
            the id of the job to send the uri
        document_uri (string)
            the uri of the document
        document_name (string)
            the name of the document
        document_format (string)
            the encoding/format of the document
        document_natural_language (string)
            if the document is a text file, what language it is in
        requesting_user_name (string)
            the user name of the job owner
        compression (string)
            the form of compression used on the file
        last_document (boolean)
            whether or not this is the last document in this job

        """

        self.assert_running()
        job = self.get_job(job_id)
        # XXX: need to validate URI
        # XXX: need to deal with the URI stream?

        #job.spool_uri(document_uri)
        #if 'dryrun' in self.config and self.config['dryrun']:
        #    job.player._dryrun = True
        #self.pending_jobs.append(job_id)
        
    @sync
    def get_job_attributes(self, job_id, requested_attributes=None):
        """RFC 2911: 3.3.4 Get-Job-Attributes Operation

        This REQUIRED operation allows a client to request the values
        of attributes of a Job object and it is almost identical to
        the Get- Printer-Attributes operation (see section 3.2.5). The
        only differences are that the operation is directed at a Job
        object rather than a Printer object, there is no
        'document-format' operation attribute used when querying a Job
        object, and the returned attribute group is a set of Job
        object attributes rather than a set of Printer object
        attributes.

        For Jobs, the possible names of attribute groups are:
          - 'job-template': the subset of the Job Template attributes
            that apply to a Job object (the first column of the table
            in Section 4.2) that the implementation supports for Job
            objects.
          - 'job-description': the subset of the Job Description
            attributes specified in Section 4.3 that the
            implementation supports for Job objects.
          - 'all': the special group 'all' that includes all
            attributes that the implementation supports for Job
            objects.

        Since a client MAY request specific attributes or named
        groups, there is a potential that there is some overlap. For
        example, if a client requests, 'job-name' and
        'job-description', the client is actually requesting the
        'job-name' attribute once by naming it explicitly, and once by
        inclusion in the 'job-description' group. In such cases, the
        Printer object NEED NOT return the attribute only once in the
        response even if it is requested multiple times. The client
        SHOULD NOT request the same attribute in multiple ways.

        It is NOT REQUIRED that a Job object support all attributes
        belonging to a group (since some attributes are
        OPTIONAL). However it is REQUIRED that each Job object support
        all these group names.

        Parameters
        ----------
        job_id (integer)
            the id of the job to send the uri
        requested_attributes (list)
            the attributes to return

        """

        self.assert_running()
        if requested_attributes is None:
            requested = self.job_attributes
        else:
            requested = [a for a in self.job_attributes \
                         if a in requested_attributes]

        _attributes = [attr.replace("-", "_") for attr in requested]
        attributes = [getattr(self, attr)(job_id) for attr in _attributes]
        return attributes

    @sync
    def set_job_attributes(self, job_id, attributes):
        self.assert_running()
        job = self.get_job(job_id)
        for attr in attributes:
            if attr in ("job-id", "job-k-octets", "job-state", "job-printer-uri"):
                raise ipp.errors.ClientErrorAttributesNotSettable(attr)
            elif attr == "job-name":
                job.name = attributes[attr]
            elif attr == "job-originating-user-name":
                job.creator = attributes[attr] # XXX: do we want this?

    @sync
    def restart_job(self, job_id, requesting_user_name=None):
        self.assert_running()
        job = self.get_job(job_id)
        try:
            job.restart()
        except InvalidJobStateException:
            # XXX
            raise ipp.errors.ClientErrorNotPossible

        self.finished_jobs.remove(job_id)
        self.pending_jobs.append(job_id)

    @sync
    def promote_job(self, job_id, requesting_user_name=None):
        # According to RFC 3998, we need to put the job at the front
        # of the queue (so that when the currently playing job
        # completes, this one will go next
        
        self.assert_running()
        job = self.get_job(job_id)
        job.priority = 1 # XXX we need to actually do something
                         # correct here
