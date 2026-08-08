# Step 1: Define the decorator function
def my_decorator(func):
    def wrapper(*args, **kwargs):
        #print(f"Before calling {func.__name__}")
        
        result = func(args[0].title(), **kwargs)
        #print(f"After calling {func.__name__}")
        return result
    return wrapper

# Step 2: Apply it using @ syntax
@my_decorator
def greet(name):
    print(f"Hello, {name}!")

# Step 3: Call the function normally
greet("nitish")