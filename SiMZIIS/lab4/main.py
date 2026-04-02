import secrets

P = 8329

def mod_pow(base: int, exp: int, mod: int) -> int:

    result = 1
    base %= mod
    while exp > 0:
        if exp & 1:
            result = (result * base) % mod
        base = (base * base) % mod
        exp >>= 1
    return result

def is_primitive_by_cycle(g: int, P: int) -> bool:

    visited = [False] * P
    val = g % P
    for k in range(1, P):
        if visited[val]:
            return False
        visited[val] = True
        val = (val * g) % P
    if visited[0]:
        return False
    for x in range(1, P):
        if not visited[x]:
            return False
    return True

def find_primitive_root(P: int) -> int:

    for g in range(2, P):
        if is_primitive_by_cycle(g, P):
            return g
    raise ValueError("Примитивный корень не найден")

def demo_diffie_hellman_and_check(P: int):
    g = find_primitive_root(P)

    print(f"Найден примитивный корень g = {g} для простого P = {P} ")

    a = secrets.randbelow(P-3) + 2
    b = secrets.randbelow(P-3) + 2
    A = mod_pow(g, a, P)
    B = mod_pow(g, b, P)
    S_A = mod_pow(B, a, P)
    S_B = mod_pow(A, b, P)

    print("\n--- Диффи-Хеллман (демонстрация) ---")
    print(f"Alice секрет a = {a}")
    print(f"Bob   секрет b = {b}")
    print(f"A = g^a mod P = {A}")
    print(f"B = g^b mod P = {B}")
    print(f"Alice вычисляет S_A = B^a mod P = {S_A}")
    print(f"Bob   вычисляет S_B = A^b mod P = {S_B}")


demo_diffie_hellman_and_check(P)

