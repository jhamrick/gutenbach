from . import verify_operations
from . import verify_printer_uri
from . import verify_requesting_username
from . import make_empty_response
from . import make_job_attributes

import logging
logger = logging.getLogger(__name__)

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
            the value supplied by the client is 'N', then only the
            first 'N' jobs are returned in the Get-Jobs Response.
            There is no mechanism to allow for the next 'M' jobs
            after the first 'N' jobs. If the client does not
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
            attribute with two values: 'job-uri' and 'job-id'.
        'which-jobs' (type2 keyword):
            The client OPTIONALLY supplies this attribute. The
            Printer object MUST support this attribute. It
            indicates which Job objects MUST be returned by the
            Printer object. The values for this attribute are:
             - 'completed': This includes any Job object whose
               state is 'completed', 'canceled', or 'aborted'.
             - 'not-completed': This includes any Job object whose
               state is 'pending', 'processing',
               'processing-stopped', or 'pending-held'.
            A Printer object MUST support both values. However, if
            the implementation does not keep jobs in the
            'completed', 'canceled', and 'aborted' states, then it
            returns no jobs when the 'completed' value is
            supplied.  If a client supplies some other value, the
            Printer object MUST copy the attribute and the
            unsupported value to the Unsupported Attributes
            response group, reject the request, and return the
            'client-error-attributes-or-values-not-supported'
            status code.  If the client does not supply this
            attribute, the Printer object MUST respond as if the
            client had supplied the attribute with a value of
            'not-completed'.
        'my-jobs' (boolean):
            The client OPTIONALLY supplies this attribute. The
            Printer object MUST support this attribute. It
            indicates whether jobs from all users or just the jobs
            submitted by the requesting user of this request MUST
            be considered as candidate jobs to be returned by the
            Printer object. If the client does not supply this
            attribute, the Printer object MUST respond as if the
            client had supplied the attribute with a value of
            'false', i.e., jobs from all users. The means for
            authenticating the requesting user and matching the
            jobs is described in section 8.

    """

    out = {}

    # generic operations verification
    attrs = verify_operations(request)

    # requested printer uri
    if 'printer-uri' not in attrs:
        raise err.ClientErrorBadRequest("Missing 'printer-uri' attribute")
    out['printer-uri'] = verify_printer_uri(attrs['printer-uri'])
    
    # requesting username
    if 'requesting-user-name' not in attrs:
        logger.warning("Missing 'requesting-user-name' attribute")
    else:
        out['requesting-user-name'] = verify_requesting_username(attrs['requesting-user-name'])

    if 'limit' in attrs:
        out['limit'] = None # XXX

    if 'requested-attributes' in attrs:
        out['requested-attributes'] = None # XXX

    if 'which-jobs' in attrs:
        out['which-jobs'] = None # XXX

    if 'my-jobs' in attrs:
        out['my-jobs'] = None # XXX

    return out

def make_get_jobs_response(jobs, request):
    """RFC 2911: 3.2.6.2 Get-Jobs Response
        
    The Printer object returns all of the Job objects up to the number
    specified by the 'limit' attribute that match the criteria as
    defined by the attribute values supplied by the client in the
    request. It is possible that no Job objects are returned since
    there may literally be no Job objects at the Printer, or there may
    be no Job objects that match the criteria supplied by the
    client. If the client requests any Job attributes at all, there is
    a set of Job Object Attributes returned for each Job object.

    It is not an error for the Printer to return 0 jobs. If the
    response returns 0 jobs because there are no jobs matching the
    criteria, and the request would have returned 1 or more jobs
    with a status code of 'successful-ok' if there had been jobs
    matching the criteria, then the status code for 0 jobs MUST be
    'successful-ok'.

    Group 1: Operation Attributes
        Status Message:
            In addition to the REQUIRED status code returned in
            every response, the response OPTIONALLY includes a
            'status-message' (text(255)) and/or a
            'detailed-status-message' (text(MAX)) operation
            attribute as described in sections 13 and 3.1.6.
        Natural Language and Character Set:
            The 'attributes-charset' and
            'attributes-natural-language' attributes as described
            in section 3.1.4.2.

    Group 2: Unsupported Attributes
        See section 3.1.7 for details on returning Unsupported
        Attributes.  The response NEED NOT contain the
        'requested-attributes' operation attribute with any
        supplied values (attribute keywords) that were requested
        by the client but are not supported by the IPP object.  If
        the Printer object does return unsupported attributes
        referenced in the 'requested-attributes' operation
        attribute and that attribute included group names, such as
        'all', the unsupported attributes MUST NOT include
        attributes described in the standard but not supported by
        the implementation.

    Groups 3 to N: Job Object Attributes
        The Printer object responds with one set of Job Object
        Attributes for each returned Job object. The Printer
        object ignores (does not respond with) any requested
        attribute or value which is not supported or which is
        restricted by the security policy in force, including
        whether the requesting user is the user that submitted the
        job (job originating user) or not (see section
        8). However, the Printer object MUST respond with the
        'unknown' value for any supported attribute (including all
        REQUIRED attributes) for which the Printer object does not
        know the value, unless it would violate the security
        policy. See the description of the 'out-of- band' values
        in the beginning of Section 4.1.

        Jobs are returned in the following order:
        - If the client requests all 'completed' Jobs (Jobs in the
          'completed', 'aborted', or 'canceled' states), then the
          Jobs are returned newest to oldest (with respect to
          actual completion time)
        - If the client requests all 'not-completed' Jobs (Jobs in
          the 'pending', 'processing', 'pending-held', and
          'processing- stopped' states), then Jobs are returned in
          relative chronological order of expected time to
          complete (based on whatever scheduling algorithm is
          configured for the Printer object).

    """

    response = make_empty_response(request)
    # XXX: we need to honor the things that the request actually asks for
    for job in jobs:
        make_job_attributes(job, request, response)
    return response
