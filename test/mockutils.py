# Utilities for checking mocking

def get_mockcall_attribute(mock_call, name):
    """Get the named attribute from a mock call.

    Python 3.6 version of:
            self.assertIsNone(mock_call.kwargs['name'])
    """
    for part_index in range(0,len(mock_call)):
        if type(mock_call[part_index]) == dict:
            kwargs = mock_call[part_index]
            if name in kwargs:
                return kwargs[name]
    raise Exception("named attribute not found: " + name)

