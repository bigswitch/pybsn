# Utilities for checking mocking


def get_mockcall_attribute(mock_call, name):
    """Get the named attribute from a mock call.

    Python 3.6 version of:
            self.assertIsNone(mock_call.kwargs['name'])
    """
    for part in mock_call:
        if isinstance(part, dict):
            if name in part:
                return part[name]
    raise Exception("named attribute not found: " + name)
