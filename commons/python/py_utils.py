#!/usr/bin/env python
def is_positive(input_string):
    input_string_lower = input_string.lower() 
    
    # return 0 when input is "yes", "true" 
    if input_string_lower in ["yes", "true"]:
        return 0
    # return 0 when input is "no", "false"
    elif input_string_lower in ["no", "false"]:
        return 1
    else:
        # return error if the input is something else
        raise ValueError("Invalid input. Please provide 'yes', 'no', 'true', or 'false'.")
