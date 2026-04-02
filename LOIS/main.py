import re
import os
import sys
from copy import deepcopy

def hogen_implication(a: float, b: float) -> float:
    """Импликация Гогена (Goguen)."""
    if a == 0.0:
        return 1.0
    if a <= b:
        return 1.0
    return b / a

def t_norm_product(x, y):
    return x * y

def parse_set(line: str):
    """
    Разбирает строку вида:
      A = <x1, 0.2> <x2, 0.8> <x3, 1>
    При ошибке печатает сообщение и завершает программу.
    Возвращает (name, {var: float, ...})
    """
    if "=" not in line:
        print(f"Ошибка: отсутствует '=' в строке множества: '{line}'")
        sys.exit(1)

    name, data = line.split("=", 1)
    name = name.strip()
    data = data.strip()

    if data.count("<") != data.count(">"):
        print(f"Ошибка: несбалансированные скобки в множестве '{name}'.")
        sys.exit(1)

    pairs = re.findall(r"<([^,>]+),\s*([^>]+)>", data)
    if not pairs:
        print(f"Ошибка: неверный формат множества '{name}'. Ожидались пары вида <x1, 0.5>.")
        sys.exit(1)

    result = {}
    first_var = pairs[0][0].strip()
    m = re.fullmatch(r"([a-zA-Z]+)(\d+)", first_var)
    if not m:
        print(f"Ошибка: некорректное имя переменной '{first_var}' в множестве '{name}'.")
        sys.exit(1)

    prefix = m.group(1)
    expected_idx = 1
    for var, val in pairs:
        var = var.strip()
        m_var = re.fullmatch(rf"{re.escape(prefix)}(\d+)", var)
        if not m_var:
            print(f"Ошибка: все переменные множества '{name}' должны начинаться с '{prefix}' (найдено '{var}').")
            sys.exit(1)
        idx_str = m_var.group(1)
        if not idx_str.isdigit():
            print(f"Ошибка: некорректный индекс в имени переменной '{var}' в множестве '{name}'.")
            sys.exit(1)
        idx = int(idx_str)
        if idx < expected_idx:
            print(f"Ошибка: переменные в множестве '{name}' должны идти по порядку "
                  f"(ожидалось {prefix} c индексом больше чем {expected_idx} или равным {expected_idx}, найдено {var}).")
            sys.exit(1)
        result[var] = float(val)
        if idx> expected_idx:
            expected_idx = idx+1
        else:
            expected_idx += 1

    return name, result


def read_input(filename: str):
    if not os.path.exists(filename):
        print(f"Ошибка: файл '{filename}' не найден.")
        sys.exit(1)
    if not os.path.isfile(filename):
        print(f"Ошибка: '{filename}' не является обычным файлом.")
        sys.exit(1)
    if not os.access(filename, os.R_OK):
        print(f"Ошибка: нет прав на чтение файла '{filename}'.")
        sys.exit(1)

    sets = {}
    rules = []

    with open(filename, "r", encoding="utf-8") as f:
        for line_no, raw_line in enumerate(f, start=1):
            line = raw_line.strip()
            if not line:
                continue
            if "~>" in line:
                parts = line.split("~>")
                if len(parts) != 2:
                    print(f"[строка {line_no}] Ошибка: неверный формат правила: '{line}'")
                    sys.exit(1)
                left, right = map(str.strip, parts)
                if not left or not right:
                    print(f"[строка {line_no}] Ошибка: пустая левая или правая часть правила: '{line}'")
                    sys.exit(1)
                rules.append((left, right))
            else:
                name, values = parse_set(line)
                sets[name] = values

    return sets, rules


# === ОСНОВНЫЕ ОПЕРАЦИИ ===

def implication_table(A, B):
    table = {}
    for x, a_val in A.items():
        table[x] = {}
        for y, b_val in B.items():
            table[x][y] = hogen_implication(a_val, b_val)
    return table

def compute_result_from_subset_using_imp_table(subset, imp_table):
    xs = sorted(imp_table.keys())
    ys = sorted(next(iter(imp_table.values())).keys())
    result = {}
    for y in ys:
        max_val = 0.0
        for x in xs:
            cell = t_norm_product(subset[x],imp_table[x][y])
            if cell > max_val:
                max_val = cell
        result[y] = max_val
    return result

def equal_sets(s1, s2, eps=1e-9):
    if set(s1.keys()) != set(s2.keys()):
        return False

    for k in s1:
        a = s1[k]
        b = s2[k]

        if a == 0 and b == 0:
            continue
        if (a == 0 and b != 0) or (a != 0 and b == 0):
            return False
        if abs(a - b) / max(abs(a), abs(b)) > eps:
            return False

    return True



# === ВЫВОД ===

def print_table(f, title, table):
    xs = sorted(list(table.keys()))
    ys = sorted(list(next(iter(table.values())).keys()))
    f.write(f"{title}\n")
    f.write("       " + "   ".join(f"{x:<10}" for x in xs) + "\n")
    for y in ys:
        f.write(f"{y:<6} " + " ".join(f"{table[x][y]:<10.6f}" for x in xs) + "\n")
    f.write("\n")

def format_result(idx, Aname, rule, label, result, same=None):
    formatted = ", ".join(f"<{y}, {v:.6f}>" for y, v in result.items())
    text = f"{idx}. {{ {Aname}, {rule} }} |~ {label} = {{{formatted}}}"
    if same:
        text += f" = {same}"
    return text


# === ГЛАВНАЯ ПРОЦЕДУРА ===

def main():
    input_filename = "input.txt"
    output_filename = "output.txt"

    sets, rules = read_input(input_filename)   
    # Очистка output.txt (создаёт файл, если его нет)
    with open(output_filename, "w", encoding="utf-8"):
        pass

    all_sets = deepcopy(sets)
    counter = 1
    new_found = True
    output_lines = []
    printed_rules = set()

    # Множество уже выполненных комбинаций (subset_name, left, right)
    processed = set()

    while new_found:
        new_found = False
        for left, right in rules:
            if left not in all_sets or right not in all_sets:
                continue

            A = all_sets[left]
            B = all_sets[right]
            imp_table_main = implication_table(A, B)

            if (left, right) not in printed_rules:
                with open(output_filename, "a", encoding="utf-8") as f:
                    print_table(f, f"{left} ~> {right}", imp_table_main)
                printed_rules.add((left, right))

            first_key_A = next(iter(A.keys()))
            m_prefix = re.match(r"([a-zA-Z]+)", first_key_A)
            left_prefix = m_prefix.group(1)
            left_vars = set(A.keys())

            # snapshot чтобы можно было безопасно добавлять в all_sets внутри цикла
            for name, subset in list(all_sets.items()):
                # Пропускаем если уже вычисляли эту комбинацию (имя подмножества, правило)
                if (name, left, right) in processed:
                    continue

                first_key = next(iter(subset.keys()))
                m_sub_prefix = re.match(r"([a-zA-Z]+)", first_key)

                subset_prefix = m_sub_prefix.group(1)
                if subset_prefix != left_prefix:
                    continue
                if set(subset.keys()) != left_vars:
                    continue

                result = compute_result_from_subset_using_imp_table(subset, imp_table_main)

                label = f"_{counter}"
                same = None
                for known_name, known_set in all_sets.items():
                    if equal_sets(result, known_set):
                        same = known_name
                        break

                output_lines.append(format_result(counter, name, f"{left} ~> {right}", label, result, same))

                # отмечаем комбинацию как обработанную, чтобы не пересчитывать её снова
                processed.add((name, left, right))

                if not same:
                    all_sets[label] = result
                    new_found = True

                counter += 1

    with open(output_filename, "a", encoding="utf-8") as f:
        for line in output_lines:
            f.write(line + "\n")

    print("Вывод завершён. Результат в output.txt")



if __name__ == "__main__":
    main()
