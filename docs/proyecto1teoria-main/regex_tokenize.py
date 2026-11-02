
def tokenize(expresion: str) -> list[str]:
    """Convierte la expresión regex en una lista de tokens de un carácter.
    Ignora espacios en blanco. Cada símbolo de operador/agrupación y cada
    operando se emite como un token independiente.
    """
    tokens = []
    for char in expresion:
        if char.isspace():
            continue
        tokens.append(char)
    return tokens
