"""Utils related to pipeline construction"""

def validate_exists(required, **kwargs):
    for arg in required:
        if not arg in kwargs:
            raise ValueError('{0} must be provided'.format(arg))
