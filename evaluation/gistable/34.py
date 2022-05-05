# -*- coding: utf-8 -*-
def calcular_dv(numero):
    """
    Función para el cálculo de el dígito de verificación utilizado en el NIT y
    CC por la DIAN Colombia.

    >>> calcular_dv(811026552)
    9
    >>> calcular_dv(890925108)
    6
    >>> calcular_dv(800197384)
    0
    >>> calcular_dv(899999034)
    1
    >>> calcular_dv(8600123361)
    6
    >>> calcular_dv(899999239)
    2
    >>> calcular_dv(890900841)
    9
    """
    coeficientes = [3, 7, 13, 17, 19, 23, 29, 37, 41, 43, 47, 53, 59, 67, 71]
    sumatoria = 0
    cnt = 0
    dv = None
    # Convierte número en string y lo itera de atras hacia adelante
    for digito in str(numero)[::-1]:
        sumatoria += int(digito) * coeficientes[cnt]
        cnt += 1
    residuo = sumatoria % 11
    if residuo > 1:
        dv = 11 - residuo
    else:
        dv = residuo
    return dv


def validar_dv(numero, dv):
    """
    Valida si el número y el dígito de verificación corresponden

    >>> validar(811026552,0)
    False
    >>> validar(890925108,6)
    True
    >>> validar(800197384,1)
    False
    >>> validar(899999034,1)
    True
    >>> validar(8600123361,3)
    False
    >>> validar(899999239,2)
    True
    >>> validar(890900841,7)
    False
    """
    return calcular_dv(numero) == dv

if __name__ == "__main__":
    import doctest
    doctest.testmod()
