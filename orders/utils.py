import random
import string

def generate_order_number():
    return "ODR" + "".join(random.choices(string.digits, k=8))
