"""Utility functions for TIC Nexus."""
import re

def format_subject(subject: str) -> str:
    """Format subject to Title Case, handling various delimiters.
    
    Example: 'computer science' -> 'Computer Science'
    'REFERENCE ONLY' -> 'Reference Only'
    'ELECTRICAL /ELECTROANICS' -> 'Electrical /Electroanics'
    'HANDBOOK :COMPUTER' -> 'Handbook :Computer'
    'CCIR-CCIT' -> 'Ccir-Ccit'
    """
    if not subject or str(subject).lower() == 'nan':
        return ""
    
    subject = str(subject).strip()
    if not subject:
        return ""
    
    # Split by common delimiters and handle each word
    # Keep the delimiters in the split results using parentheses in regex
    parts = re.split(r'([\s\-/:\(\)\.,])', subject)
    formatted_parts = []
    for part in parts:
        if not part:
            continue
            
        # Check if part contains alphanumeric characters
        if any(c.isalnum() for c in part):
            # Find the first alphanumeric character
            for i, char in enumerate(part):
                if char.isalnum():
                    # Capitalize the first letter found and lowercase the rest of the word
                    # Only lowercase if the rest is all uppercase (to preserve some internal casing if needed, 
                    # but usually we want to enforce uniformity as requested)
                    # The user asked for uniformity, so we'll enforce Title Case strictly.
                    formatted_parts.append(part[:i] + part[i:].capitalize())
                    break
        else:
            # It's a delimiter or whitespace
            formatted_parts.append(part)
    
    return "".join(formatted_parts)
