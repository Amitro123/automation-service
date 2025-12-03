"""Test file with real code changes to trigger automation."""


def test_function():
    """This is a test function to trigger code review."""
    print("Testing webhook automation flow")
    print("This should trigger full automation")
    print("Because it has more than 10 lines")
    print("And contains actual code changes")
    
    # Add some logic
    result = 0
    for i in range(10):
        result += i
    
    return result


if __name__ == "__main__":
    print(f"Result: {test_function()}")
