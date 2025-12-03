"""Test module to trigger Jules code review with substantial changes."""


def calculate_fibonacci(n: int) -> int:
    """Calculate the nth Fibonacci number using recursion.
    
    Args:
        n: The position in the Fibonacci sequence
        
    Returns:
        The nth Fibonacci number
    """
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    else:
        return calculate_fibonacci(n - 1) + calculate_fibonacci(n - 2)


def factorial(n: int) -> int:
    """Calculate factorial of n.
    
    Args:
        n: Non-negative integer
        
    Returns:
        Factorial of n
    """
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    if n == 0 or n == 1:
        return 1
    return n * factorial(n - 1)


class MathOperations:
    """A class for performing various mathematical operations."""
    
    def __init__(self):
        """Initialize the MathOperations class."""
        self.history = []
    
    def add(self, a: float, b: float) -> float:
        """Add two numbers.
        
        Args:
            a: First number
            b: Second number
            
        Returns:
            Sum of a and b
        """
        result = a + b
        self.history.append(f"add({a}, {b}) = {result}")
        return result
    
    def multiply(self, a: float, b: float) -> float:
        """Multiply two numbers.
        
        Args:
            a: First number
            b: Second number
            
        Returns:
            Product of a and b
        """
        result = a * b
        self.history.append(f"multiply({a}, {b}) = {result}")
        return result
    
    def get_history(self) -> list:
        """Get the history of operations.
        
        Returns:
            List of operation strings
        """
        return self.history.copy()


if __name__ == "__main__":
    # Test Fibonacci
    print("Fibonacci sequence:")
    for i in range(10):
        print(f"F({i}) = {calculate_fibonacci(i)}")
    
    # Test factorial
    print("\nFactorials:")
    for i in range(6):
        print(f"{i}! = {factorial(i)}")
    
    # Test MathOperations
    print("\nMath Operations:")
    math = MathOperations()
    print(f"5 + 3 = {math.add(5, 3)}")
    print(f"4 * 7 = {math.multiply(4, 7)}")
    print(f"History: {math.get_history()}")
