from .safe_stringify import safe_stringify

# TODO: hash code did not change when I changed an utterance 
def hash_code(input_obj):
    """
    Generate a hash code for an object
    Source: https://stackoverflow.com/questions/7616461/generate-a-hash-from-string-in-javascript
    """
    text = safe_stringify(input_obj)
    hash_val = 0

    if len(text) == 0:
        return hash_val

    for i in range(len(text)):
        chr_code = ord(text[i])
        hash_val = ((hash_val << 5) - hash_val) + chr_code
        hash_val = hash_val & 0xFFFFFFFF  # Convert to 32bit integer

    # Convert to signed 32-bit integer
    if hash_val & 0x80000000:
        hash_val = -((hash_val ^ 0xFFFFFFFF) + 1)

    return hash_val
