
import os
import secrets
from math import gcd

# ----------------- НАСТРОЙКИ (редактируйте здесь) -----------------
P_VALUE = None        # Задайте p (int) или None для генерации
Q_VALUE = None        # Задайте q (int) или None для генерации
E_VALUE = 65537       # Открытая экспонента
PRIME_BITS = 1024     # Минимальная битовая длина p и q

PUB_FILE = 'pubkey.txt'
PRIV_FILE = 'privkey.txt'
MESSAGE_FILE = 'message.txt'   # текстовый: одно целое m на строку, 0 <= m < n
SIGN_FILE = 'signature.txt'    # текстовый: одно целое s на строку
CIPHER_FILE = 'cipher.txt'     # текстовый: одно целое c на строку
# ------------------------------------------------------------------

# ---------- Математические вспомогательные функции ----------

def modular_pow(base: int, exponent: int, modulus: int) -> int:
    if modulus == 1:
        return 0
    result = 1
    base = base % modulus
    e = exponent
    while e > 0:
        if e & 1:
            result = (result * base) % modulus
        base = (base * base) % modulus
        e >>= 1
    return result


def egcd(a: int, b: int):
    if b == 0:
        return (a, 1, 0)
    else:
        g, x1, y1 = egcd(b, a % b)
        x = y1
        y = x1 - (a // b) * y1
        return (g, x, y)


def modinv(a: int, m: int) -> int:
    g, x, y = egcd(a, m)
    if g != 1:
        raise ValueError('modular inverse does not exist — e и phi(n) не взаимно просты')
    return x % m


# ---------- Тест простоты и генерация простых (Miller-Rabin) ----------

def is_probable_prime(n: int, k: int = 40) -> bool:
    if n < 2:
        return False
    small_primes = [2,3,5,7,11,13,17,19,23,29]
    for p in small_primes:
        if n % p == 0:
            return n == p
    s = 0
    d = n - 1
    while d % 2 == 0:
        d //= 2
        s += 1
    for _ in range(k):
        a = secrets.randbelow(n - 3) + 2
        x = modular_pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(s - 1):
            x = (x * x) % n
            if x == n - 1:
                break
        else:
            return False
    return True


def generate_prime(bits: int) -> int:
    if bits < 2:
        raise ValueError('bits must be >= 2')
    while True:
        candidate = secrets.randbits(bits) | (1 << (bits - 1)) | 1
        if is_probable_prime(candidate):
            return candidate


# ---------- Чтение/запись ключей (plain text key=value) ----------

def save_pub_plain(pub: dict, filename: str):
    with open(filename, 'w') as f:
        f.write(f"e={pub['e']}\n")
        f.write(f"n={pub['n']}")


def save_priv_plain(priv: dict, filename: str):

    with open(filename, 'w') as f:
        f.write(f"d={priv['d']}\n")
        f.write(f"n={priv['n']}")


def parse_integer_lines(path: str) -> list:
    """Читает текстовый файл и возвращает список целых чисел, игнорируя пустые строки и комментарии (#)."""
    vals = []
    with open(path, 'r') as f:
        for lineno, line in enumerate(f, start=1):
            s = line.strip()
            if not s or s.startswith('#'):
                continue
            try:
                v = int(s, 10)
            except ValueError:
                raise ValueError(f'Невалидное целое в {path} на строке {lineno}: {s}')
            vals.append(v)
    return vals


def write_integer_lines(path: str, ints: list):
    with open(path, 'w') as f:
        for v in ints:
            f.write(str(v) + '')


# ---------- Формирование ключей из p,q,e ----------

def build_keys_from_pqe(p: int, q: int, e: int):
    if p == q:
        raise ValueError('p и q не должны быть равны')
    if not is_probable_prime(p):
        raise ValueError('p не является вероятным простым')
    if not is_probable_prime(q):
        raise ValueError('q не является вероятным простым')
    if p.bit_length() < PRIME_BITS or q.bit_length() < PRIME_BITS:
        raise ValueError(f'p и q должны иметь не менее {PRIME_BITS} бит')
    n = p * q
    phi = (p - 1) * (q - 1)
    if gcd(e, phi) != 1:
        raise ValueError('e и phi(n) не взаимно просты')
    d = modinv(e, phi)
    pub = {'e': e, 'n': n}
    priv = {'d': d, 'n': n, 'p': p, 'q': q}
    return pub, priv


# ---------- Операции: подпись, шифрование, расшифрование, проверка ----------

def sign_integers(priv: dict, message_ints: list) -> list:
    n = priv['n']
    d = priv['d']
    sigs = []
    for m in message_ints:
        if m < 0 or m >= n:
            raise ValueError(f'Значение m вне диапазона 0..n-1: {m}')
        s = modular_pow(m, d, n)
        sigs.append(s)
    return sigs


def encrypt_integers(pub: dict, message_ints: list) -> list:
    n = pub['n']
    e = pub['e']
    cts = []
    for m in message_ints:
        if m < 0 or m >= n:
            raise ValueError(f'Значение m вне диапазона 0..n-1: {m}')
        c = modular_pow(m, e, n)
        cts.append(c)
    return cts


def decrypt_integers(priv: dict, cipher_ints: list) -> list:
    n = priv['n']
    d = priv['d']
    recovered = []
    for c in cipher_ints:
        if c < 0 or c >= n:
            raise ValueError(f'Значение ciphertext вне диапазона 0..n-1: {c}')
        m = modular_pow(c, d, n)
        recovered.append(m)
    return recovered


def verify_integer_signatures(pub: dict, message_ints: list, sigs: list) -> bool:
    if len(message_ints) != len(sigs):
        raise ValueError('Количество сообщений и подписей не совпадает')
    e = pub['e']
    n = pub['n']
    for i, (m, s) in enumerate(zip(message_ints, sigs), start=1):
        m_star = modular_pow(s, e, n)
        if m_star != m:
            print(f'Ошибка проверки подписи в записи #{i}: m != s^e mod n (m={m}, m*={m_star})')
            return False
    return True


def verify_encryption_roundtrip(priv: dict, original_ints: list, cipher_ints: list) -> bool:
    """Проверяет, что для каждого c: decrypt(c) == исходное m.
    Возвращает True если все верно, иначе False и выводит первые несоответствия."""
    if len(original_ints) != len(cipher_ints):
        raise ValueError('Количество исходных чисел и шифротекстов не совпадает')
    recovered = decrypt_integers(priv, cipher_ints)
    bad = 0
    for i, (m_orig, m_rec) in enumerate(zip(original_ints, recovered), start=1):
        if m_orig != m_rec:
            print(f'Ошибка расшифровки в записи #{i}: исходное m={m_orig}, восстановленное m={m_rec}')
            bad += 1
            if bad >= 10:
                print('Показаны первые 10 ошибок, остальных пропускаем')
                break
    if bad == 0:
        print('Проверка шифрования: все шифротексты корректно расшифровываются в исходные значения')
        return True
    else:
        print(f'Проверка шифрования завершена: найдено {bad} несоответствий')
        return False


# ---------- Главный автоматический сценарий ----------
if __name__ == '__main__':
    # 1) Подготовка p,q,e
    p = P_VALUE
    q = Q_VALUE
    e = E_VALUE
    if p is None:
        print('Генерация p...')
        p = generate_prime(PRIME_BITS)
        print(f'p сгенерирован ({p.bit_length()} бит)')
    if q is None:
        print('Генерация q...')
        q = generate_prime(PRIME_BITS)
        print(f'q сгенерирован ({q.bit_length()} бит)')

    print('Формирование ключей из p, q, e...')
    pub, priv = build_keys_from_pqe(p, q, e)
    n_bitlen = pub['n'].bit_length()
    print(f'n = p * q (битность n = {n_bitlen})')

    # 2) Сохранение ключей
    save_pub_plain(pub, PUB_FILE)
    save_priv_plain(priv, PRIV_FILE)
    print(f'Ключи сохранены: {PUB_FILE}, {PRIV_FILE}')

    # 3) Чтение/создание MESSAGE_FILE (текстовый, целые на строку)
    if not os.path.exists(MESSAGE_FILE):
        # создаём пример: 5 случайных чисел в диапазоне 0..n-1
        sample = [secrets.randbelow(pub['n']) for _ in range(5)]
        write_integer_lines(MESSAGE_FILE, sample)
        print(f'Файл сообщения {MESSAGE_FILE} не найден — создан пример ({len(sample)} чисел)')

    message_ints = parse_integer_lines(MESSAGE_FILE)
    print(f'Прочитано {len(message_ints)} целых из {MESSAGE_FILE}')

    # 4) Подпись каждого m: s = m^d mod n
    sigs = sign_integers(priv, message_ints)
    write_integer_lines(SIGN_FILE, sigs)
    print(f'Подписи сохранены в {SIGN_FILE} ({len(sigs)} записей)')

    # 5) Шифрование каждого m: c = m^e mod n
    cts = encrypt_integers(pub, message_ints)
    write_integer_lines(CIPHER_FILE, cts)
    print(f'Зашифрованные числа сохранены в {CIPHER_FILE} ({len(cts)} записей)')

    # 6) Проверка подписей
    ok_sig = verify_integer_signatures(pub, message_ints, sigs)
    if ok_sig:
        print('Все подписи корректны')
    else:
        print('Есть неверные подписи')

    # 7) Проверка шифрования/расшифрования (как в методическом тексте):
    ok_enc = verify_encryption_roundtrip(priv, message_ints, cts)
    if ok_enc:
        print('Проверка шифрования пройдена — расшифровка возвращает исходные m')
    else:
        print('Проверка шифрования выявила несоответствия — проверьте p,q,e и входные данные')

    print('Готово. Файлы:')
    print(f'  Открытый ключ:  {PUB_FILE}')
    print(f'  Приватный ключ: {PRIV_FILE}')
    print(f'  Исходное сообщение (целые): {MESSAGE_FILE}')
    print(f'  Подписи (целые): {SIGN_FILE}')
    print(f'  Зашифрованные числа: {CIPHER_FILE}')
