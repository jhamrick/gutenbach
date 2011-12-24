from job_template_attributes import *
from job_description_attributes import *
from printer_description_attributes import *
from operation_attributes import *

__all__ = ['job_template_attributes',
           'job_description_attributes',
           'printer_description_attributes',
           'operation_attributes']
__all__.extend(job_template_attributes.__all__)
__all__.extend(job_description_attributes.__all__)
__all__.extend(printer_description_attributes.__all__)
__all__.extend(operation_attributes.__all__)
