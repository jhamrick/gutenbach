from .errors import InvalidJobException, InvalidPrinterStateException, InvalidJobStateException
from .job import GutenbachJob
from gutenbach.ipp import PrinterStates as States
import gutenbach.ipp as ipp
import logging
import time
import threading
import traceback
import sys
import tempfile
from . import sync


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
        self.assert_running()
        return ipp.PrinterUriSupported(self.uri)
    @printer_uri_supported.setter
    def printer_uri_supported(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("printer-uri-supported")

    @property
    def uri_authentication_supported(self):
        self.assert_running()
        return ipp.UriAuthenticationSupported("none")
    @uri_authentication_supported.setter
    def uri_authentication_supported(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("uri-authentication-supported")

    @property
    def uri_security_supported(self):
        self.assert_running()
        return ipp.UriSecuritySupported("none")
    @uri_security_supported.setter
    def uri_security_supported(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("uri-security-supported")

    @property
    def printer_name(self):
        self.assert_running()
        return ipp.PrinterName(self.name)
    @printer_name.setter
    def printer_name(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("printer-name")

    @property
    def printer_state(self):
        self.assert_running()
        return ipp.PrinterState(self.state)
    @printer_state.setter
    def printer_state(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("printer-state")

    @property
    def printer_state_reasons(self):
        self.assert_running()
        return ipp.PrinterStateReasons("none")
    @printer_state_reasons.setter
    def printer_state_reasons(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("printer-state-reasons")

    @property
    def ipp_versions_supported(self):
        self.assert_running()
        return ipp.IppVersionsSupported(*self.config['ipp-versions'])
    @ipp_versions_supported.setter
    def ipp_versions_supported(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("ipp-versions-supported")

    # XXX: We should query ourself for the supported operations
    @property
    def operations_supported(self):
        self.assert_running()
        return ipp.OperationsSupported(ipp.OperationCodes.GET_JOBS)
    @operations_supported.setter
    def operations_supported(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("operations-supported")

    @property
    def charset_configured(self):
        self.assert_running()
        return ipp.CharsetConfigured("utf-8") # XXX
    @charset_configured.setter
    def charset_configured(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("charset-configured")
        
    @property
    def charset_supported(self):
        self.assert_running()
        return ipp.CharsetSupported("utf-8") # XXX
    @charset_supported.setter
    def charset_supported(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("charset-supported")

    @property
    def natural_language_configured(self):
        self.assert_running()
        return ipp.NaturalLanguageConfigured("en-us")
    @natural_language_configured.setter
    def natural_language_configured(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("natural-language-configured")

    @property
    def generated_natural_language_supported(self):
        self.assert_running()
        return ipp.GeneratedNaturalLanguageSupported("en-us")
    @generated_natural_language_supported.setter
    def generated_natural_language_supported(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("generated-natural-language-supported")

    @property
    def document_format_default(self):
        self.assert_running()
        return ipp.DocumentFormatDefault("application/octet-stream")
    @document_format_default.setter
    def document_format_default(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("document-format-default")

    @property
    def document_format_supported(self):
        self.assert_running()
        return ipp.DocumentFormatSupported("application/octet-stream", "audio/mp3")
    @document_format_supported.setter
    def document_format_supported(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("document-format-supported")

    @property
    def printer_is_accepting_jobs(self):
        self.assert_running()
        return ipp.PrinterIsAcceptingJobs(True)
    @printer_is_accepting_jobs.setter
    def printer_is_accepting_jobs(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("printer-is-accepting-jobs")

    @property
    def queued_job_count(self):
        self.assert_running()
        return ipp.QueuedJobCount(len(self.active_jobs))
    @queued_job_count.setter
    def queued_job_count(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("queued-job-count")

    @property
    def pdl_override_supported(self):
        self.assert_running()
        return ipp.PdlOverrideSupported("not-attempted")
    @pdl_override_supported.setter
    def pdl_override_supported(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("pdl-override-supported")

    @property
    def printer_up_time(self):
        self.assert_running()
        return ipp.PrinterUpTime(int(time.time()) - self.time_created)
    @printer_up_time.setter
    def printer_up_time(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("printer-up-time")

    @property
    def compression_supported(self):
        self.assert_running()
        return ipp.CompressionSupported("none")
    @compression_supported.setter
    def compression_supported(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("compression-supported")

    @property
    def multiple_operation_time_out(self):
        self.assert_running()
        return ipp.MultipleOperationTimeOut(240)
    @multiple_operation_time_out.setter
    def multiple_operation_time_out(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("multiple-operation-time-out")

    @property
    def multiple_document_jobs_supported(self):
        self.assert_running()
        return ipp.MultipleDocumentJobsSupported(False)
    @multiple_document_jobs_supported.setter
    def multiple_document_jobs_supported(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("multiple-document-jobs-supported")

    ######################################################################
    ###                      Job IPP Attributes                        ###
    ######################################################################

    def job_id(self, job_id):
        self.assert_running()
        job = self.get_job(job_id)
        return ipp.JobId(job.id)

    def job_name(self, job_id):
        self.assert_running()
        job = self.get_job(job_id)
        return ipp.JobName(job.name)

    def job_originating_user_name(self, job_id):
        self.assert_running()
        job = self.get_job(job_id)
        return ipp.JobOriginatingUserName(job.creator)

    def job_k_octets(self, job_id):
        self.assert_running()
        job = self.get_job(job_id)
        return ipp.JobKOctets(job.size)

    def job_state(self, job_id):
        self.assert_running()
        job = self.get_job(job_id)
        return ipp.JobState(job.state)

    def job_printer_uri(self, job_id):
        self.assert_running()
        job = self.get_job(job_id)
        return ipp.JobPrinterUri(self.uri)

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
