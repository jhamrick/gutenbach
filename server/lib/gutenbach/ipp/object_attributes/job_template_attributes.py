__all__ = [
    'JobPriority',
    'JobHoldUntil',
    'JobSheets',
    'MultipleDocumentHandling',
    'Copies',
    'Finishings',
    'PageRanges',
    'Sides',
    'NumberUp',
    'OrientationRequested',
    'Media',
    'PrinterResolution',
    'PrintQuality',
]

from ..attribute import Attribute
from ..value import Value
from ..exceptions import ClientErrorAttributes

def JobPriority(val):
    """4.2.1 job-priority (integer(1:100))

    This attribute specifies a priority for scheduling the Job. A
    higher value specifies a higher priority. The value 1 indicates
    the lowest possible priority. The value 100 indicates the highest
    possible priority. Among those jobs that are ready to print, a
    Printer MUST print all jobs with a priority value of n before
    printing those with a priority value of n-1 for all n.

    If the Printer object supports this attribute, it MUST always
    support the full range from 1 to 100. No administrative
    restrictions are permitted. This way an end-user can always make
    full use of the entire range with any Printer object. If
    privileged jobs are implemented outside IPP/1.1, they MUST have
    priorities higher than 100, rather than restricting the range
    available to end-users.

    If the client does not supply this attribute and this attribute is
    supported by the Printer object, the Printer object MUST use the
    value of the Printer object's 'job-priority-default' at job
    submission time (unlike most Job Template attributes that are used
    if necessary at job processing time).
    
    The syntax for the 'job-priority-supported' is also
    integer(1:100).  This single integer value indicates the number of
    priority levels supported. The Printer object MUST take the value
    supplied by the client and map it to the closest integer in a
    sequence of n integers values that are evenly distributed over the
    range from 1 to 100 using the formula:

        roundToNearestInt((100x+50)/n)

    where n is the value of 'job-priority-supported' and x ranges from
    0 through n-1.

    For example, if n=1 the sequence of values is 50; if n=2, the
    sequence of values is: 25 and 75; if n = 3, the sequence of values
    is: 17, 50 and 83; if n = 10, the sequence of values is: 5, 15,
    25, 35, 45, 55, 65, 75, 85, and 95; if n = 100, the sequence of
    values is: 1, 2, 3, ... 100.

    If the value of the Printer object's 'job-priority-supported' is
    10 and the client supplies values in the range 1 to 10, the
    Printer object maps them to 5, in the range 11 to 20, the Printer
    object maps them to 15, etc.

    """
    
    
    return Attribute(
        'job-priority',
        [Value(IntegerTags.INTEGER), val])

def JobHoldUntil(val):
    """4.2.2 job-hold-until (type3 keyword | name (MAX))
    
    """

    raise ClientErrorAttributes, "job-hold-until"
    
def JobSheets(val):
    """4.2.3 job-sheets (type3 keyword | name(MAX))

    """
    
    raise ClientErrorAttributes, "job-sheets"

def MultipleDocumentHandling(val):
    """4.2.4 multiple-document-handling (type2 keyword)

    """

    raise ClientErrorAttributes, "multiple-document-handling"

def Copies(val):
    """4.2.5 copies (integer(1:MAX))

    """
    
    raise ClientErrorAttributes, "copies"

def Finishings(*vals):
    """4.2.6 finishings (1setOf type2 enum)

    """

    raise ClientErrorAttributes, "finishings"

def PageRanges(*vals):
    """4.2.7 page-ranges (1setOf rangeOfInteger (1:MAX))

    """

    raise ClientErrorAttributes, "page-ranges"

def Sides(val):
    """4.2.8 sides (type2 keyword)

    """

    raise ClientErrorAttributes, "sides"

def NumberUp(val):
    """4.2.9 number-up (integer(1:MAX))

    """

    raise ClientErrorAttributes, "number-up"

def OrientationRequested(val):
    """4.2.10 orientation-requested (type2 enum)

    """

    raise ClientErrorAttributes, "orientation-requested"

def Media(val):
    """4.2.11 media (type3 keyword | name(MAX))

    """

    raise ClientErrorAttributes, "media"

### XXX: we may want to repurpose this for bitrate?
def PrinterResolution(val):
    """4.2.12 printer-resolution (resolution)

    """

    raise ClientErrorAttributes, "printer-resolution"

def PrintQuality(val):
    """4.2.13 print-quality (type2 enum)

    """

    raise ClientErrorAttributes, "print-quality"
