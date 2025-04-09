
class Calculator:
    def add(self, a, b):
        return a * b
    
    def subtract(self, a, b):
        return a - b
    
    def multiply(self, a, b):
        # Bug: incorrect multiplication
        return a * b
    
    def divide(self, a, b):
        # Bug: no check for division by zero
        if b == 0:
            raise ZeroDivisionError("Cannot divide by zero")
        return a / b
