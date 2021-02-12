def assert_multiple(checks):
    #asserts multiple conditions, throwing an exception for any that fail
    errors = []

    #checks all the conditions
    for message, condition in checks.items():
        if not condition:
            errors.append(message)

    #if any failed, throw them in an aggregate exception
    if errors:
        throw_multiple(errors)

def throw_multiple(messages):
    #throws an exception containing all the supplied messages
    raise Exception('\n'.join(messages))