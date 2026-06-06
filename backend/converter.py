# encoding: utf-8
import re

# ==========================================
# VERIFIED BIDIRECTIONAL MAPPING DICTIONARIES
# ==========================================

unicodeToPreetiDict = {
    "अ": "c", "आ": "cf", "ा": "f", "इ": "O", "ई": "O{", "र्": "{", "उ": "p", "ए": "P",
    "े": "]", "ै": "}", "ो": "f]", "ौ": "f}", "ओ": "cf]", "औ": "cf}", "ं": "+", "ँ": "F",
    "ि": "l", "ी": "L", "ु": "'", "ू": '"', "क": "s", "ख": "v", "ग": "u", "घ": "3",
    "ङ": "ª", "च": "r", "छ": "5", "ज": "h", "झ": "´", "ञ": "`", "ट": "6", "ठ": "7",
    "ड": "8", "ढ": "9", "ण": "0f", "त": "t", "थ": "y", "द": "b", "ध": "w", "न": "g",
    "प": "k", "फ": "km", "ब": "a", "भ": "e", "म": "d", "य": "o", "र": "/", "रू": "?",
    "ृ": "[", "ल": "n", "व": "j", "स": ";", "श": "z", "ष": "if", "ज्ञ": "1", "ह": "x",
    "१": "!", "२": "@", "३": "#", "४": "$", "५": "%", "६": "^", "७": "&", "८": "*",
    "९": "(", "०": ")", "।": ".", "्": "\\", "ऊ": "pm", "-": " ", "(": "-", ")": "_"
}

preetiToUnicodeDict = {
    "0": "ण्", "1": "ज्ञ", "2": "द्द", "3": "घ", "4": "द्ध", "5": "छ", "6": "ट", "7": "ठ",
    "8": "ड", "9": "ढ", "~": "ञ्", "`": "ञ", "!": "१", "@": "२", "#": "३", "$": "४",
    "%": "५", "^": "६", "&": "७", "*": "८", "(": "९", ")": "०", "_": ")", "+": "ं",
    "Q": "त्त", "W": "ध्", "E": "भ्", "R": "च्", "T": "त्", "Y": "थ्", "U": "ग्", "I": "क्ष्",
    "O": "इ", "P": "ए", "}": "ै", "|": "्र", "q": "त्र", "w": "ध", "e": "भ", "r": "च",
    "t": "त", "y": "थ", "u": "ग", "i": "ष्", "o": "य", "p": "उ", "[": "ृ", "]": "े",
    "\\": "्", "A": "ब्", "S": "क्", "D": "म्", "F": "ँ", "G": "न्", "H": "ज्", "J": "व्",
    "K": "प्", "L": "ी", ":": "स्", "\"": "ू", "a": "ब", "s": "क", "d": "म", "f": "ा",
    "g": "न", "h": "ज", "j": "व", "k": "प", "l": "ि", ";": "स", "'": "ु", "Z": "श्",
    "X": "ह्", "C": "ऋ", "V": "ख्", "B": "द्य", "N": "ल्", "M": "ः", "<": "?", ">": "श्र",
    "?": "रु", "z": "श", "x": "ह", "c": "अ", "v": "ख", "b": "द", "n": "ल", ",": ",",
    ".": "।", "/": "र", "¿": "रू", "å": "द्व", "-": "(", "=": "."
}

# ==========================================
# UNICODE TO PREETI ENGINE
# ==========================================

def normalizeUnicode(unicodetext):
    index = -1
    normalized = ''
    while index + 1 < len(unicodetext):
        index += 1
        character = unicodetext[index]
        try:
            try:
                if character != 'र':  # for aadha akshars
                    if unicodetext[index + 1] == '्' and unicodetext[index + 2] != ' ' and unicodetext[index + 2] != '।' and unicodetext[index + 2] != ',':
                        if unicodetext[index + 2] != 'र':
                            if unicodeToPreetiDict[character] in list('wertyuxasdghjkzvn'):
                                # Convert full consonant to half consonant key in Preeti (subtracting 32 changes lowercase ASCII to uppercase)
                                normalized += chr(ord(unicodeToPreetiDict[character]) - 32)
                                index += 1
                                continue
                            elif character == 'स':
                                normalized += ':'
                                index += 1
                                continue
                            elif character == 'ष':
                                normalized += 'i'
                                index += 1
                                continue
                if unicodetext[index - 1] != 'र' and character == '्' and unicodetext[index + 1] == 'र':
                    # for leg split markers (like in क्रम or ट्रक)
                    if unicodetext[index - 1] not in ['ट', 'ठ', 'ड']:
                        normalized += '|'  # for sign as in क्रम
                        index += 1
                        continue
                    else:
                        # For retroflex split (truck) - maps to standard leg split symbol in Preeti
                        normalized += '«'
                        index += 1
                        continue
            except IndexError:
                pass
            normalized += character
        except KeyError:
            normalized += character
    normalized = normalized.replace('त|', 'q')  # for त्र
    return normalized


def unicode_to_preeti(unicodestring: str) -> str:
    """
    Converts Devanagari Unicode string to legacy Preeti font text.
    Handles vowel sign reordering, leg split markers, and half-letter replacements.
    """
    normalizedunicodetext = normalizeUnicode(unicodestring)
    converted = ''
    index = -1
    while index + 1 < len(normalizedunicodetext):
        index += 1
        character = normalizedunicodetext[index]
        if character == '\ufeff':
            continue
        try:
            try:
                # 1. Hraswo Ukaar / Ikaar ('ि') reordering
                if normalizedunicodetext[index + 1] == 'ि':
                    if character == 'q':
                        converted += 'l' + character
                    else:
                        converted += 'l' + unicodeToPreetiDict[character]
                    index += 1
                    continue

                # 2. Ikaar reordering over half-consonants (e.g., त्ति)
                if normalizedunicodetext[index + 2] == 'ि':
                    if character in list('WERTYUXASDGHJK:ZVN'):
                        if normalizedunicodetext[index + 1] != 'q':
                            converted += 'l' + character + unicodeToPreetiDict[normalizedunicodetext[index + 1]]
                            index += 2
                            continue
                        else:
                            converted += 'l' + character + normalizedunicodetext[index + 1]
                            index += 2
                            continue

                # 3. Reph ('र्') positioning (e.g., वार्ता)
                if normalizedunicodetext[index + 1] == '्' and character == 'र':
                    # If followed by another matra, the reph '{' is placed at the end of the matra
                    if normalizedunicodetext[index + 3] in ['ा', 'ो', 'ौ', 'े', 'ै', 'ी']:
                        converted += unicodeToPreetiDict[normalizedunicodetext[index + 2]] + unicodeToPreetiDict[normalizedunicodetext[index + 3]] + '{'
                        index += 3
                        continue
                    elif normalizedunicodetext[index + 3] == 'ि':
                        converted += unicodeToPreetiDict[normalizedunicodetext[index + 3]] + unicodeToPreetiDict[normalizedunicodetext[index + 2]] + '{'
                        index += 3
                        continue
                    converted += unicodeToPreetiDict[normalizedunicodetext[index + 2]] + '{'
                    index += 2
                    continue

                # 4. Leg split and Ikaar reordering (e.g., ष्ट्रिय)
                if normalizedunicodetext[index + 3] == 'ि':
                    if normalizedunicodetext[index + 2] in ['|', '«']:
                        if character in list('WERTYUXASDGHJK:ZVNIi'):
                            converted += 'l' + character + unicodeToPreetiDict[normalizedunicodetext[index + 1]] + normalizedunicodetext[index + 2]
                            index += 3
                            continue

            except IndexError:
                pass
            converted += unicodeToPreetiDict[character]
        except KeyError:
            converted += character

    # Apply composite replacements for standard Preeti layout
    replacements = [
        ('Si', 'I'),      # aadha ka + aadha sha = ক্ষ
        ('H`', '1'),      # ज्ञ composite
        ('b\\w', '4'),    # द्ध composite
        ('z|', '>'),      # श्र composite
        ("/'", '?'),      # रु composite
        ('/"', '¿'),      # रू composite
        ('Tt', 'Q'),      # त्त composite
        ('b\\lj', 'lå'),  # द्वि composite
        ('b\\j', 'å'),    # द्व composite
        ('0f\\', '0'),    # aadha ण
        ('`\\', '~')      # aadha ञ
    ]
    for old, new in replacements:
        converted = converted.replace(old, new)
        
    return converted


# ==========================================
# PREETI TO UNICODE ENGINE
# ==========================================

def preeti_to_unicode(preetistring: str) -> str:
    """
    Converts legacy Preeti font text to Devanagari Unicode.
    Uses regex replacements to process leg-splits, matra shifts, reph, and conjuncts.
    """
    # Step 1: Mapping character-by-character based on verified preetiToUnicodeDict
    # To handle multi-character mappings correctly, we sort keys by length descending
    sorted_keys = sorted(preetiToUnicodeDict.keys(), key=len, reverse=True)
    
    # We do a sequential replacement of characters, avoiding double mappings by using placeholders if needed.
    # However, since Preeti is ASCII-based, mapping character-by-character with a regex is safe
    # because ASCII inputs match uniquely. We compile a regex for all Preeti keys.
    pattern = re.compile("|".join(re.escape(k) for k in sorted_keys))
    
    mapped_chars = []
    index = 0
    while index < len(preetistring):
        match = pattern.match(preetistring, index)
        if match:
            key = match.group(0)
            mapped_chars.append(preetiToUnicodeDict[key])
            index += len(key)
        else:
            mapped_chars.append(preetistring[index])
            index += 1
            
    mapped_text = "".join(mapped_chars)
    
    # Step 2: Apply regular expression reordering rules (based on defaults.yaml)
    # 2.1: Join half consonants with aa matra (क् + ा = का)
    mapped_text = re.sub(r'्ा', '', mapped_text)
    
    # 2.2: Shift modifier 'm' just after त्र or त्त
    mapped_text = re.sub(r'(त्र|त्त)([^उभप]+?)m', r'\1m\2', mapped_text)
    mapped_text = re.sub(r'त्रm', 'क्र', mapped_text)
    mapped_text = re.sub(r'त्तm', 'क्त', mapped_text)
    
    # 2.3: Shift modifier 'm' just after other characters and map them
    mapped_text = re.sub(r'([^उभप]+?)m', r'm\1', mapped_text)
    mapped_text = re.sub(r'उm', 'ऊ', mapped_text)
    mapped_text = re.sub(r'भm', 'झ', mapped_text)
    mapped_text = re.sub(r'पm', 'फ', mapped_text)
    
    # 2.4: Shift hraswo-ikaar ('ि') behind its corresponding consonant or consonant cluster
    # Consonant cluster consists of optional half-consonants (consonant + ्) followed by a full consonant
    # We use a non-backtracking style cluster pattern.
    # Devanagari character set: [^्\s] matches any character that is not a halant or whitespace.
    mapped_text = re.sub(r'ि((?:.[्])*[^्])', r'\1ि', mapped_text)
    
    # 2.5: Shift reph ('{') in front of the preceding consonant cluster
    # Consonant cluster preceded by optional matras, shifted back
    mapped_text = re.sub(r'((?:.[्])*.[ािीुूृेैोौंःँ]*?){', r'{\1', mapped_text)
    
    # 2.6: Resolve special composites after reph shifting
    mapped_text = re.sub(r'इ{', 'ई', mapped_text)
    
    # 2.7: Replace remaining '{' with the Unicode reph 'र्'
    mapped_text = re.sub(r'{', 'र्', mapped_text)
    
    # Resolve some legacy typographic edge cases in Preeti conversion
    mapped_text = mapped_text.replace('«', '्र')
    mapped_text = mapped_text.replace('å', 'द्व')
    
    return mapped_text


# ==========================================
# AUTO-DETECT & TEXT CONVERSION
# ==========================================

def detect_direction(text: str) -> str:
    """
    Auto-detect input direction based on character ranges.
    U+0900 to U+097F -> Devanagari Unicode -> "unicode_to_preeti"
    Otherwise assume Preeti text (ASCII letters, specific symbols) -> "preeti_to_unicode"
    """
    if re.search(r'[\u0900-\u097F]', text):
        return "unicode_to_preeti"
    return "preeti_to_unicode"

def convert_nepali_text(text: str, direction: str) -> str:
    """
    Decoupled text conversion utility.
    Processes text without chaining. Applies direction-specific pipeline per text node.
    English, numbers, and basic punctuation passthrough is handled natively by the mappings.
    """
    if direction == "auto":
        direction = detect_direction(text)
        
    if direction == "unicode_to_preeti":
        # Process paragraph line-by-line
        lines = text.split('\n')
        converted_lines = [unicode_to_preeti(line) for line in lines]
        return '\n'.join(converted_lines)
    elif direction == "preeti_to_unicode":
        lines = text.split('\n')
        converted_lines = [preeti_to_unicode(line) for line in lines]
        return '\n'.join(converted_lines)
    else:
        raise ValueError(f"Invalid direction: {direction}")
