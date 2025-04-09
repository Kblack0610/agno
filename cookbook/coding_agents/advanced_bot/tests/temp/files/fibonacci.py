
def calculate_fibonacci(n):
    """
    Calculate Fibonacci sequence up to n terms.
    
    Args:
        n: Number of terms to generate
        
    Returns:
        List of Fibonacci numbers
    """
    fibonacci = [0, 1]
    
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    
    for i in range(2, n):
        fibonacci.append(fibonacci[i-1] + fibonacci[i-2])
    
    return fibonacci
