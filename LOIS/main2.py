import re
from copy import deepcopy

# === БАЗОВЫЕ ФУНКЦИИ ===

def t_norm_product(x, y):
    return x * y

def hogen_implication(a: float, b: float) -> float:
    """Импликация Гогена (Goguen)."""
    # Защита от tiny rounding: если a == 0 считаем 1.0
    if a == 0.0:
        return 1.0
    if a <= b:
        return 1.0
    return b / a


# === ВСПОМОГАТЕЛЬНЫЕ ===

def parse_set(line):
    """
    Разбирает строку вида:
      A = <x1, 0.2> <x2, 0.8> <x3, 1>
    Проверяет:
      - сбалансированные скобки
      - пары вида <name, число>
      - единый префикс переменных и последовательность индексов
    Возвращает (name, {var: float, ...})
    """
    name, data = line.split("=", 1)
    name = name.strip()
    data = data.strip()

    if data.count("<") != data.count(">"):
        raise ValueError(f"Ошибка: несбалансированные скобки в множестве '{name}'.")

    pairs = re.findall(r"<([^,>]+),\s*([^>]+)>", data)
    if not pairs:
        raise ValueError(f"Ошибка: неверный формат множества '{name}'. Ожидались пары вида <x1, 0.5>.")

    result = {}
    first_var = pairs[0][0].strip()
    m = re.fullmatch(r"([a-zA-Z]+)(\d+)", first_var)
    if not m:
        raise ValueError(f"Ошибка: некорректное имя переменной '{first_var}' в множестве '{name}'.")

    prefix = m.group(1)
    expected_idx = 1
    for var, val in pairs:
        var = var.strip()
        m = re.fullmatch(rf"{prefix}(\d+)", var)
        if not m:
            raise ValueError(f"Ошибка: все переменные множества '{name}' должны начинаться с '{prefix}' (найдено '{var}').")
        idx = int(m.group(1))
        if idx != expected_idx:
            raise ValueError(f"Ошибка: переменные в множестве '{name}' должны идти по порядку "
                             f"({prefix}{expected_idx} ожидалось, найдено {var}).")
        try:
            result[var] = float(val)
        except ValueError:
            raise ValueError(f"Ошибка: неверное значение '{val}' в множестве '{name}'.")
        expected_idx += 1

    return name, result


def read_input(filename):
    sets = {}
    rules = []
    with open(filename, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                if "~>" in line:
                    left, right = map(str.strip, line.split("~>"))
                    rules.append((left, right))
                else:
                    name, values = parse_set(line)
                    sets[name] = values
            except Exception as e:
                raise ValueError(f"[строка {line_no}] {e}")
    return sets, rules


# === ОСНОВНЫЕ ОПЕРАЦИИ ===

def implication_table(A, B):
    """
    Возвращает таблицу импликации в виде dict:
      { x_i: { y_j: I(a_i, b_j), ... }, ... }
    где x_i - переменные из A (левая часть), y_j - переменные из B (правая).
    """
    table = {}
    for x, a_val in A.items():
        table[x] = {}
        for y, b_val in B.items():
            table[x][y] = hogen_implication(a_val, b_val)
    return table

def compute_result_from_subset_using_imp_table(subset, imp_table):
    """
    По описанному алгоритму:
    - subset: {x_i: val_i} (факт, переменные совпадают с левой частью правила)
    - imp_table: таблица I(x_i, y_j) с x_i как ключами
    Алгоритм:
      1) Для каждого x_i умножаем всю колонку imp_table[x_i] на subset[x_i].
      2) Для каждого y_j берём максимум по всем x_i (max по строке) -> result[y_j]
    Возвращает result: {y_j: value}
    """
    # проверка согласованности индексов столбцов
    xs = sorted(imp_table.keys())
    ys = sorted(next(iter(imp_table.values())).keys())

    # Для каждого y: вычисляем максимум по x из (subset[x] * imp_table[x][y])
    result = {}
    for y in ys:
        max_val = 0.0
        for x in xs:
            if x not in subset:
                # если отсутствует x в подмножестве — считаем как 0 (или можно бросать ошибку)
                continue
            cell = subset[x] * imp_table[x][y]
            if cell > max_val:
                max_val = cell
        result[y] = max_val
    return result

def equal_sets(s1, s2, eps=1e-12):
    if set(s1.keys()) != set(s2.keys()):
        return False
    return all(abs(s1[k] - s2[k]) < eps for k in s1)


# === ВЫВОД ===

def print_table(f, title, table):
    """
    Печатает таблицу импликации:
    - верхняя строка: переменные левого множества (A) (x1, x2, ...)
    - первая колонка: переменные правого множества (B) (y1, y2, ...)
    Формат: 6 знаков после точки при выводе.
    """
    xs = sorted(list(table.keys()))      # x-переменные (A) — сверху
    ys = sorted(list(next(iter(table.values())).keys()))  # y-переменные (B) — слева
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
    try:
        sets, rules = read_input("input.txt")
    except ValueError as e:
        print("❌ Ошибка во входных данных:")
        print(e)
        return

    all_sets = deepcopy(sets)
    counter = 1
    new_found = True
    output_lines = []

    printed_rules = set()  # чтобы не дублировать таблицы
    open("output.txt", "w").close()

    while new_found:
        new_found = False
        for left, right in rules:
            if left not in all_sets or right not in all_sets:
                # правило не может быть применено пока нет соответствующего множества
                continue

            A = all_sets[left]
            B = all_sets[right]

            # Строим таблицу импликации по A и B один раз
            imp_table_main = implication_table(A, B)

            # Печатаем таблицу импликации только один раз для правила
            if (left, right) not in printed_rules:
                with open("output.txt", "a", encoding="utf-8") as f:
                    print_table(f, f"{left} ~> {right}", imp_table_main)
                printed_rules.add((left, right))

            # префикс и точное требование: подставляем только множества,
            # у которых префикс совпадает и сами переменные совпадают с A
            left_prefix = re.match(r"([a-zA-Z]+)", next(iter(A.keys()))).group(1)
            left_vars = set(A.keys())

            for name, subset in list(all_sets.items()):
                # проверяем префикс
                first_key = next(iter(subset.keys()))
                subset_prefix = re.match(r"([a-zA-Z]+)", first_key).group(1)
                if subset_prefix != left_prefix:
                    continue
                # проверяем, что набор переменных тот же самый (точное совпадение)
                if set(subset.keys()) != left_vars:
                    # пропускаем факты, у которых отличаются индексы/количество
                    continue

                # По заданному алгоритму: умножаем значения из subset на соответствующие столбцы
                result = compute_result_from_subset_using_imp_table(subset, imp_table_main)

                label = f"_{counter}"
                same = None
                for known_name, known_set in all_sets.items():
                    if equal_sets(result, known_set):
                        same = known_name
                        break

                output_lines.append(format_result(counter, name, f"{left} ~> {right}", label, result, same))

                if not same:
                    all_sets[label] = result
                    new_found = True

                counter += 1

    # Записываем результаты шагов вывода (список формул)
    with open("output.txt", "a", encoding="utf-8") as f:
        for line in output_lines:
            f.write(line + "\n")

    print("Вывод завершён. Результат в output.txt")


if __name__ == "__main__":
    main()
