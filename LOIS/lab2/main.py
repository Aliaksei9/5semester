import itertools
import sys


class Interval:
    """Класс для представления непрерывного интервала [start, end]."""

    def __init__(self, start, end):
        self.start = float(start)
        self.end = float(end)

    def intersect(self, other):
        """Возвращает пересечение двух интервалов или None."""
        new_start = max(self.start, other.start)
        new_end = min(self.end, other.end)
        if new_start > new_end + 1e-9:
            return None
        return Interval(new_start, new_end)

    def contains(self, other):
        """Проверяет, содержится ли интервал 'other' полностью внутри этого."""
        return self.start <= other.start + 1e-9 and self.end >= other.end - 1e-9

    def is_point(self):
        return abs(self.end - self.start) < 1e-9

    def __eq__(self, other):
        return abs(self.start - other.start) < 1e-9 and abs(self.end - other.end) < 1e-9

    def __repr__(self):
        if self.is_point():
            return f"{self.start:g}"
        return f"[{self.start:g}, {self.end:g}]"


class SolutionVector:
    """Класс для представления одного варианта решения."""

    def __init__(self, intervals):
        self.intervals = intervals  # {index_variable: Interval}

    def get_subset_status(self, other):
        """
        1: self содержит other, -1: other содержит self, 0: нет полного вложения
        """
        self_contains_other = True
        other_contains_self = True

        for k in self.intervals:
            if not self.intervals[k].contains(other.intervals[k]):
                self_contains_other = False
            if not other.intervals[k].contains(self.intervals[k]):
                other_contains_self = False

        if self_contains_other: return 1
        if other_contains_self: return -1
        return 0

    def intersect(self, other):
        new_intervals = {}
        for k in self.intervals:
            inter = self.intervals[k].intersect(other.intervals[k])
            if inter is None:
                return None
            new_intervals[k] = inter
        return SolutionVector(new_intervals)


def validate_indices(names_list, prefix):
    """
    Проверяет, что имена переменных имеют формат {prefix}{int}
    и идут в строго возрастающем порядке индексов.
    """
    indices = []
    for name in names_list:
        if not name.startswith(prefix):
            raise ValueError(f"Переменная '{name}' должна начинаться с '{prefix}'")
        try:
            # Извлекаем часть после префикса и пробуем превратить в число
            idx_str = name[len(prefix):]
            idx = int(idx_str)
            indices.append(idx)
        except ValueError:
            raise ValueError(f"Переменная '{name}' не содержит корректного числового индекса")

    # Проверка на возрастание
    for i in range(len(indices) - 1):
        if indices[i] >= indices[i + 1]:
            raise ValueError(
                f"Нарушен порядок индексов для {prefix}: "
                f"{names_list[i]} идет перед {names_list[i + 1]} "
                f"({indices[i]} >= {indices[i + 1]})"
            )


def parse_input(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            lines = [l.strip() for l in f if l.strip()]

        if len(lines) < 4:
            raise ValueError("Файл слишком короткий")

        # line 0: имена Y (y1 y2 y3)
        y_names = lines[0].split()
        validate_indices(y_names, 'y')  # <-- ПРОВЕРКА 1

        # line 1: значения B
        b_values = [float(x) for x in lines[1].split()]

        if len(y_names) != len(b_values):
            raise ValueError(
                f"Количество переменных Y ({len(y_names)}) не совпадает с количеством значений ({len(b_values)})")

        # line 2: имена X (x1 x2)
        x_names = lines[2].split()
        validate_indices(x_names, 'x')  # <-- ПРОВЕРКА 2
        num_x = len(x_names)

        # line 3+: матрица
        matrix = []
        for l in lines[3:]:
            row = [float(x) for x in l.split()]
            if len(row) != num_x:
                raise ValueError("Неверное количество столбцов в матрице")
            matrix.append(row)

        if len(matrix) != len(b_values):
            raise ValueError("Размер матрицы не совпадает с вектором B")

        return x_names, b_values, matrix
    except ValueError as ve:
        print(f"Ошибка валидации данных: {ve}")
        sys.exit(1)
    except Exception as e:
        print(f"Ошибка чтения файла: {e}")
        sys.exit(1)


def solve_row(row_vals, b_val, num_vars):
    """Находит решения для одной строки: max(min(x, r)) = b"""
    solutions = []
    potential_pivots = [i for i, r in enumerate(row_vals) if r >= b_val]

    if not potential_pivots:
        return []

    for pivot_idx in potential_pivots:
        current_intervals = {}

        # Условия для опорного элемента
        r_pivot = row_vals[pivot_idx]
        if r_pivot > b_val:
            current_intervals[pivot_idx] = Interval(b_val, b_val)
        else:
            current_intervals[pivot_idx] = Interval(b_val, 1.0)

        # Условия для остальных
        for i in range(num_vars):
            if i == pivot_idx: continue
            r_i = row_vals[i]
            if r_i > b_val:
                current_intervals[i] = Interval(0.0, b_val)
            else:
                current_intervals[i] = Interval(0.0, 1.0)

        solutions.append(SolutionVector(current_intervals))

    return solutions


def write_results(filename, final_vectors, x_names):
    """Форматирует решения и записывает их в файл."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            if not final_vectors:
                f.write("Решений нет\n")
                return

            # Группировка для вывода (Union)
            display_groups = []
            for vec in final_vectors:
                new_group = {k: [vec.intervals[k]] for k in vec.intervals}
                display_groups.append(new_group)

            # Слияние похожих групп
            changed = True
            while changed:
                changed = False
                to_remove = set()
                for i in range(len(display_groups)):
                    if i in to_remove: continue
                    for j in range(i + 1, len(display_groups)):
                        if j in to_remove: continue

                        g1 = display_groups[i]
                        g2 = display_groups[j]

                        diff_count = 0
                        diff_key = -1
                        keys = g1.keys()

                        for k in keys:
                            s1 = sorted([str(x) for x in g1[k]])
                            s2 = sorted([str(x) for x in g2[k]])
                            if s1 != s2:
                                diff_count += 1
                                diff_key = k

                        if diff_count == 1:
                            g1[diff_key].extend(g2[diff_key])
                            g1[diff_key].sort(key=lambda x: x.start)
                            to_remove.add(j)
                            changed = True

                display_groups = [g for idx, g in enumerate(display_groups) if idx not in to_remove]

            # Запись в файл
            for group in display_groups:
                parts = []
                for k_idx in range(len(x_names)):
                    intervals = group[k_idx]
                    int_strs = [str(inv) for inv in intervals]
                    val_str = " ∪ ".join(int_strs)

                    relation = "=" if (len(intervals) == 1 and intervals[0].is_point()) else "∊"
                    parts.append(f"{x_names[k_idx]} {relation} {val_str}")

                f.write(", ".join(parts) + ";\n")

        print(f"Результат успешно записан в {filename}")

    except Exception as e:
        print(f"Ошибка записи файла: {e}")


def main():
    x_names, b_values, matrix = parse_input('input.txt')
    num_vars = len(x_names)

    # 1. Решения для каждой строки
    rows_solutions = []
    for i, b_val in enumerate(b_values):
        row_sol = solve_row(matrix[i], b_val, num_vars)
        if not row_sol:
            write_results('output.txt', [], x_names)
            return
        rows_solutions.append(row_sol)

    # 2. Пересечение всех строк
    final_solutions = []
    for combo in itertools.product(*rows_solutions):
        current_intersection = combo[0]
        valid_combo = True

        for i in range(1, len(combo)):
            current_intersection = current_intersection.intersect(combo[i])
            if current_intersection is None:
                valid_combo = False
                break

        if valid_combo:
            final_solutions.append(current_intersection)

    if not final_solutions:
        write_results('output.txt', [], x_names)
        return

    # 3. Очистка от вложенных интервалов
    indices_to_remove = set()
    for i in range(len(final_solutions)):
        if i in indices_to_remove: continue
        for j in range(len(final_solutions)):
            if i == j or j in indices_to_remove: continue

            status = final_solutions[i].get_subset_status(final_solutions[j])
            if status == 1:
                indices_to_remove.add(j)
            elif status == -1:
                indices_to_remove.add(i)
                break

    cleaned_solutions = [final_solutions[i] for i in range(len(final_solutions)) if i not in indices_to_remove]

    # 4. Запись
    write_results('output.txt', cleaned_solutions, x_names)


if __name__ == "__main__":
    main()