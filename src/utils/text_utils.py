from config import RLM, LRM

def reverse_hebrew_text(text):
    """Reverse Hebrew text characters while preserving word order"""
    return text[::-1]

def format_rtl_text(text):
    return f'{RLM}{text}{RLM}'

def hebrew_sort_key(member):
    """
    Key function for sorting Hebrew names from right to left
    """
    lastname_reversed = member['Lastname']
    firstname_reversed = member['Firstname']
    return (lastname_reversed, firstname_reversed)