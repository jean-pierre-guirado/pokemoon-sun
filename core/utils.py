import unicodedata


def normaliser(txt):
    """Supprime les accents et met en minuscules."""
    if not txt:
        return ""
    return "".join(
        c for c in unicodedata.normalize('NFD', str(txt))
        if unicodedata.category(c) != 'Mn'
    ).lower().strip()
