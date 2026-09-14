# To Create the Base62 utility
# Using Base62 lets us represent numbers using these 62 characters, producing compact codes

import string

ALPHABET = string.digits + string.ascii_lowercase + string.ascii_uppercase


def encode(number: int) -> str:
    if number == 0:
        return ALPHABET[0]

    base = len(ALPHABET)
    result = []

    while number > 0:
        number, remainder = divmod(number, base)#number÷base,quotient=number and remainder=remainder
        result.append(ALPHABET[remainder])

    return "".join(reversed(result))