import mysql.connector
from mysql.connector import Error
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime, timedelta


class Database:
    def __init__(self):
        self.connection = None
        self.connect()

    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host='localhost',
                database='lab2',
                user='root',  # Replace with your MySQL username
                password='19802005aA@Aa'  # Replace with your MySQL password
            )
        except Error as e:
            print(f"Error connecting to MySQL: {e}")

    def execute_query(self, query, params=None, fetch=False, commit=False, lastid=False):
        if self.connection is None or not self.connection.is_connected():
            self.connect()
        cursor = self.connection.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            if fetch:
                result = cursor.fetchall()
                return result
            if commit:
                self.connection.commit()
            if lastid:
                return cursor.lastrowid
            return True
        except Error as e:
            print(f"Error executing query: {e}")
            return False
        finally:
            cursor.close()

    def call_procedure(self, proc_name, params):
        if self.connection is None or not self.connection.is_connected():
            self.connect()
        cursor = self.connection.cursor()
        try:
            cursor.callproc(proc_name, params)
            self.connection.commit()
            return True
        except Error as e:
            print(f"Error calling procedure: {e}")
            return False
        finally:
            cursor.close()

    def call_function(self, func_name, params):
        query = f"SELECT {func_name}({', '.join(['%s'] * len(params))})"
        result = self.execute_query(query, params, fetch=True)
        return result[0][0] if result else 0

    def get_subdivision_id(self, name):
        query = "SELECT ID_Подразделения FROM Подразделение WHERE Название_подразделения = %s"
        result = self.execute_query(query, (name,), fetch=True)
        return result[0][0] if result else None

    def get_worker_subdivision(self, worker_id):
        query = """
            SELECT ID_Подразделения
            FROM Учёт_работы
            WHERE Номер_работника = %s
            ORDER BY Дата_начала_работы DESC
            LIMIT 1
        """
        result = self.execute_query(query, (worker_id,), fetch=True)
        return result[0][0] if result else None

    # 1. Добавление нового устройства
    def add_device(self, inv_num, name, model, year, subdivision, date):
        sub_id = self.get_subdivision_id(subdivision)
        if not sub_id:
            return False
        query_device = """
            INSERT INTO Устройство (Инвентарный_номер, Название_устройства, Модель, Год_выпуска, Списание)
            VALUES (%s, %s, %s, %s, 0)
        """
        if not self.execute_query(query_device, (inv_num, name, model, year), commit=True):
            return False
        query_move = """
            INSERT INTO Перемещение_устройства (Инвентарный_номер, Дата_перемещения, ID_Подразделения)
            VALUES (%s, %s, %s)
        """
        return self.execute_query(query_move, (inv_num, date, sub_id), commit=True)

    # 2. Редактирование информации о устройстве
    def edit_device(self, inv_num, field, value):
        if field == 'name':
            field = 'Название_устройства'
        elif field == 'model':
            field = 'Модель'
        elif field == 'year':
            field = 'Год_выпуска'
        else:
            return False
        query = f"UPDATE Устройство SET {field} = %s WHERE Инвентарный_номер = %s"
        return self.execute_query(query, (value, inv_num), commit=True)

    # 3. Перемещение устройств
    def move_device(self, inv_num, date, new_sub):
        sub_id = self.get_subdivision_id(new_sub)
        if not sub_id:
            return False
        query = """
            INSERT INTO Перемещение_устройства (Инвентарный_номер, Дата_перемещения, ID_Подразделения)
            VALUES (%s, %s, %s)
        """
        return self.execute_query(query, (inv_num, date, sub_id), commit=True)

    # 4. Передача в ремонт
    def send_to_repair(self, date, from_worker, to_worker, inv_num):
        return self.call_procedure('send_it_to_repairs', [date, from_worker, to_worker, inv_num])

    # 5. Редактирование сотрудника
    def edit_worker(self, worker_num, field, value, date=None):
        if field in ['Фамилия', 'Имя', 'Отчество', 'Год_рождения', 'Пол']:
            if field == 'Пол':
                value = 1 if value.lower() == 'мужской' else 0
            query = f"UPDATE Работник SET {field} = %s WHERE Номер_работника = %s"
            return self.execute_query(query, (value, worker_num), commit=True)
        elif field == 'Должность':
            query = "UPDATE Работник SET Должность = %s WHERE Номер_работника = %s"
            if not self.execute_query(query, (value, worker_num), commit=True):
                return False
            if date:
                sub_id = self.get_worker_subdivision(worker_num)
                if not sub_id:
                    return False
                end_date = datetime.strptime(date, '%Y-%m-%d') + timedelta(hours=8)
                query_log = """
                    INSERT INTO Учёт_работы (Номер_работника, Дата_начала_работы, Дата_окончания_работы, ID_Подразделения, Должность)
                    VALUES (%s, %s, %s, %s, %s)
                """
                return self.execute_query(query_log,
                                          (worker_num, date, end_date.strftime('%Y-%m-%d %H:%M:%S'), sub_id, value),
                                          commit=True)
            return True
        elif field == 'Подразделение':
            if not date:
                return False
            sub_id = self.get_subdivision_id(value)
            if not sub_id:
                return False
            end_date = datetime.strptime(date, '%Y-%m-%d') + timedelta(hours=8)
            query_log = """
                INSERT INTO Учёт_работы (Номер_работника, Дата_начала_работы, Дата_окончания_работы, ID_Подразделения, Должность)
                VALUES (%s, %s, %s, %s, (SELECT Должность FROM Работник WHERE Номер_работника = %s))
            """
            return self.execute_query(query_log,
                                      (worker_num, date, end_date.strftime('%Y-%m-%d %H:%M:%S'), sub_id, worker_num),
                                      commit=True)
        return False

    # 6. Добавление сотрудника
    def add_worker(self, gender, surname, name, patronymic, birth_year, subdivision, position, start_date):
        sub_id = self.get_subdivision_id(subdivision)
        if not sub_id:
            return False
        gender_bool = 1 if gender.lower() == 'мужской' else 0
        query_worker = """
            INSERT INTO Работник (Фамилия, Имя, Отчество, Год_рождения, Пол, Должность)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        worker_id = self.execute_query(query_worker, (surname, name, patronymic, birth_year, gender_bool, position),
                                       commit=True, lastid=True)
        if not worker_id:
            return False
        base_date = datetime.strptime(start_date, '%Y-%m-%d')
        start_datetime = base_date + timedelta(hours=8)
        end_datetime = start_datetime + timedelta(hours=8)
        query_log = """
            INSERT INTO Учёт_работы (Номер_работника, Дата_начала_работы, Дата_окончания_работы, ID_Подразделения, Должность)
            VALUES (%s, %s, %s, %s, %s)
        """
        return self.execute_query(query_log, (
        worker_id, start_datetime.strftime('%Y-%m-%d %H:%M:%S'), end_datetime.strftime('%Y-%m-%d %H:%M:%S'), sub_id,
        position), commit=True)

    # 7. Удаление сотрудника
    def delete_worker(self, worker_num):
        query = "DELETE FROM Работник WHERE Номер_работника = %s"
        return self.execute_query(query, (worker_num,), commit=True)

    # 8. Список сотрудников по возрасту и полу
    def list_workers_by_age_gender(self, age, gender):
        gender_bool = 1 if gender.lower() == 'мужской' else 0
        current_year = datetime.now().year
        birth_year_limit = current_year - age
        query = """
            SELECT * FROM Работник
            WHERE Год_рождения < %s AND Пол = %s
        """
        return self.execute_query(query, (birth_year_limit, gender_bool), fetch=True)

    # 9. Список сотрудников по подразделению
    def list_workers_by_subdivision(self, sub_name):
        sub_id = self.get_subdivision_id(sub_name)
        if not sub_id:
            return []
        query = """
            SELECT w.*
            FROM Работник w
            JOIN Учёт_работы l ON w.Номер_работника = l.Номер_работника
            WHERE l.ID_Подразделения = %s
            AND l.Дата_начала_работы = (
                SELECT MAX(Дата_начала_работы)
                FROM Учёт_работы
                WHERE Номер_работника = w.Номер_работника
            )
        """
        return self.execute_query(query, (sub_id,), fetch=True)

    # 10. Подразделение с max сданной техникой
    def max_repair_subdivision(self):
        query_subs = "SELECT Название_подразделения FROM Подразделение WHERE ID_Подразделения != 1"
        subs = [row[0] for row in self.execute_query(query_subs, fetch=True)]
        max_count = 0
        max_sub = None
        for sub in subs:
            count = self.call_function('count_sent_to_repair', [sub])
            if count > max_count:
                max_count = count
                max_sub = sub
        return max_sub, max_count

    # 11. Количество техники за 3 года
    def count_devices_three_years(self, sub_name, dev_name):
        current_year = datetime.now().year
        total = 0
        for y in range(current_year - 2, current_year + 1):
            total += self.call_function('count_devices_in_subdivision_year', [sub_name, dev_name, y])
        return total

    # 12. Учёт работы
    def add_work_log(self, worker_num, start_date, end_date, sub_name, position):
        sub_id = self.get_subdivision_id(sub_name)
        if not sub_id:
            return False
        query = """
            INSERT INTO Учёт_работы (Номер_работника, Дата_начала_работы, Дата_окончания_работы, ID_Подразделения, Должность)
            VALUES (%s, %s, %s, %s, %s)
        """
        return self.execute_query(query, (worker_num, start_date, end_date, sub_id, position), commit=True)

    # 13. Принять в ремонт
    def take_for_repair(self, repairer, details, date, cost, repair_id, type_repair):
        return self.call_procedure('take_it_for_repair', [repairer, details, date, cost, repair_id, type_repair])

    # 14. Закончить ремонт
    def finish_repair_proc(self, date, writeoff, repair_id):
        writeoff_bool = 1 if writeoff else 0
        return self.call_procedure('finish_repair', [date, writeoff_bool, repair_id])

    def get_table_data(self, table_name):
        query = f"SELECT * FROM `{table_name}`"
        return self.execute_query(query, fetch=True)

    def get_table_columns(self, table_name):
        query = f"SHOW COLUMNS FROM `{table_name}`"
        result = self.execute_query(query, fetch=True)
        return [row[0] for row in result] if result else []


class View:
    def __init__(self, root):
        self.root = root
        self.root.title("Lab2 Application")
        self.root.geometry("1920x1080")
        self.create_db_view()
        self.create_main_menu()

    def create_db_view(self):
        db_frame = tk.Frame(self.root)
        db_frame.pack(pady=10)

        tk.Label(db_frame, text="Просмотр данных в БД").pack()

        self.table_var = tk.StringVar()
        tables = ['Подразделение', 'Работник', 'Устройство', 'Перемещение_устройства', 'Учёт_работы', 'Накладная',
                  'Ремонт']
        self.table_combo = ttk.Combobox(db_frame, textvariable=self.table_var, values=tables)
        self.table_combo.pack()

        load_btn = tk.Button(db_frame, text="Загрузить таблицу", command=self.load_table)
        load_btn.pack(pady=5)

        self.tree = ttk.Treeview(self.root)
        self.tree.pack(fill=tk.BOTH, expand=True, pady=10)

    def load_table(self):
        table = self.table_var.get()
        if not table:
            return
        data = self.controller.model.get_table_data(table)
        columns = self.controller.model.get_table_columns(table)
        self.tree.delete(*self.tree.get_children())
        self.tree['columns'] = columns
        self.tree['show'] = 'headings'
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        for row in data:
            self.tree.insert('', tk.END, values=row)

    def create_main_menu(self):
        menu_frame = tk.Frame(self.root)
        menu_frame.pack(pady=20)

        buttons = [
            ("1. Добавить устройство", self.add_device_form),
            ("2. Редактировать устройство", self.edit_device_form),
            ("3. Переместить устройство", self.move_device_form),
            ("4. Передать в ремонт", self.send_to_repair_form),
            ("5. Редактировать сотрудника", self.edit_worker_form),
            ("6. Добавить сотрудника", self.add_worker_form),
            ("7. Удалить сотрудника", self.delete_worker_form),
            ("8. Список по возрасту и полу", self.list_by_age_gender_form),
            ("9. Список по подразделению", self.list_by_subdivision_form),
            ("10. Лидер по ремонтам", self.max_repair_sub),
            ("11. Количество техники за 3 года", self.count_devices_form),
            ("12. Учёт работы", self.add_work_log_form),
            ("13. Принять в ремонт", self.take_for_repair_form),
            ("14. Закончить ремонт", self.finish_repair_form)
        ]

        for text, command in buttons:
            tk.Button(menu_frame, text=text, command=command).pack(fill=tk.X, pady=5)

    def get_input(self, title, fields):
        window = tk.Toplevel(self.root)
        window.title(title)
        entries = {}
        for field in fields:
            tk.Label(window, text=field).pack()
            entry = tk.Entry(window)
            entry.pack()
            entries[field] = entry
        submit_btn = tk.Button(window, text="Выполнить")
        submit_btn.pack(pady=10)
        return window, entries, submit_btn

    def show_result(self, message):
        messagebox.showinfo("Result", message)

    def show_list(self, data, columns):
        window = tk.Toplevel(self.root)
        tree = ttk.Treeview(window, columns=columns, show='headings')
        for col in columns:
            tree.heading(col, text=col)
        for row in data:
            tree.insert('', tk.END, values=row)
        tree.pack()

    # Forms
    def add_device_form(self):
        fields = ["Инвентарный номер", "Название устройства", "Модель", "Год выпуска", "Подразделение",
                  "Дата ввода (YYYY-MM-DD)"]
        window, entries, btn = self.get_input("Добавить устройство", fields)

        def submit():
            success = self.controller.add_device(
                int(entries["Инвентарный номер"].get()),
                entries["Название устройства"].get(),
                entries["Модель"].get(),
                int(entries["Год выпуска"].get()),
                entries["Подразделение"].get(),
                entries["Дата ввода (YYYY-MM-DD)"].get()
            )
            self.show_result("Успех" if success else "Ошибка")
            if success:
                window.destroy()

        btn.config(command=submit)

    def edit_device_form(self):
        window = tk.Toplevel(self.root)
        window.title("Редактировать устройство")
        tk.Label(window, text="Инвентарный номер").pack()
        inv_entry = tk.Entry(window)
        inv_entry.pack()

        tk.Label(window, text="Поле").pack()
        field_var = tk.StringVar()
        field_combo = ttk.Combobox(window, textvariable=field_var, values=['name', 'model', 'year'])
        field_combo.pack()

        tk.Label(window, text="Новое значение").pack()
        value_entry = tk.Entry(window)
        value_entry.pack()

        btn = tk.Button(window, text="Выполнить")

        def submit():
            value = value_entry.get() if field_var.get() != 'year' else int(value_entry.get())
            success = self.controller.edit_device(
                int(inv_entry.get()),
                field_var.get(),
                value
            )
            self.show_result("Успех" if success else "Ошибка")
            if success:
                window.destroy()

        btn.config(command=submit)
        btn.pack(pady=10)

    def move_device_form(self):
        fields = ["Инвентарный номер", "Дата перемещения (YYYY-MM-DD)", "Новое подразделение"]
        window, entries, btn = self.get_input("Переместить устройство", fields)

        def submit():
            success = self.controller.move_device(
                int(entries["Инвентарный номер"].get()),
                entries["Дата перемещения (YYYY-MM-DD)"].get(),
                entries["Новое подразделение"].get()
            )
            self.show_result("Успех" if success else "Ошибка")
            if success:
                window.destroy()

        btn.config(command=submit)

    def send_to_repair_form(self):
        fields = ["Дата (YYYY-MM-DD)", "Номер сдавшего", "Номер принявшего", "Инвентарный номер"]
        window, entries, btn = self.get_input("Передать в ремонт", fields)

        def submit():
            success = self.controller.send_to_repair(
                entries["Дата (YYYY-MM-DD)"].get(),
                int(entries["Номер сдавшего"].get()),
                int(entries["Номер принявшего"].get()),
                int(entries["Инвентарный номер"].get())
            )
            self.show_result("Успех" if success else "Ошибка")
            if success:
                window.destroy()

        btn.config(command=submit)

    def edit_worker_form(self):
        window = tk.Toplevel(self.root)
        window.title("Редактировать сотрудника")

        tk.Label(window, text="Номер работника").pack()
        num_entry = tk.Entry(window)
        num_entry.pack()

        tk.Label(window, text="Поле").pack()
        field_var = tk.StringVar()
        field_combo = ttk.Combobox(window, textvariable=field_var,
                                   values=['Фамилия', 'Имя', 'Отчество', 'Год_рождения', 'Пол', 'Должность',
                                           'Подразделение'])
        field_combo.pack()

        tk.Label(window, text="Новое значение").pack()
        value_entry = tk.Entry(window)
        value_entry.pack()

        date_label = tk.Label(window, text="Дата (YYYY-MM-DD)")
        date_entry = tk.Entry(window)

        def toggle_date(*args):
            if field_var.get() in ['Должность', 'Подразделение']:
                date_label.pack()
                date_entry.pack()
            else:
                date_label.pack_forget()
                date_entry.pack_forget()

        field_combo.bind("<<ComboboxSelected>>", toggle_date)

        btn = tk.Button(window, text="Выполнить")

        def submit():
            success = self.controller.edit_worker(
                int(num_entry.get()),
                field_var.get(),
                value_entry.get(),
                date_entry.get() if field_var.get() in ['Должность', 'Подразделение'] else None
            )
            self.show_result("Успех" if success else "Ошибка")
            if success:
                window.destroy()

        btn.config(command=submit)
        btn.pack(pady=10)

    def add_worker_form(self):
        window = tk.Toplevel(self.root)
        window.title("Добавить сотрудника")

        tk.Label(window, text="Пол").pack()
        gender_var = tk.StringVar()
        gender_combo = ttk.Combobox(window, textvariable=gender_var, values=['мужской', 'женский'])
        gender_combo.pack()

        tk.Label(window, text="Фамилия").pack()
        surname_entry = tk.Entry(window)
        surname_entry.pack()

        tk.Label(window, text="Имя").pack()
        name_entry = tk.Entry(window)
        name_entry.pack()

        tk.Label(window, text="Отчество").pack()
        patronymic_entry = tk.Entry(window)
        patronymic_entry.pack()

        tk.Label(window, text="Год рождения").pack()
        birth_entry = tk.Entry(window)
        birth_entry.pack()

        tk.Label(window, text="Подразделение").pack()
        sub_entry = tk.Entry(window)
        sub_entry.pack()

        tk.Label(window, text="Должность").pack()
        pos_entry = tk.Entry(window)
        pos_entry.pack()

        tk.Label(window, text="Дата начала (YYYY-MM-DD)").pack()
        start_entry = tk.Entry(window)
        start_entry.pack()

        btn = tk.Button(window, text="Выполнить")

        def submit():
            success = self.controller.add_worker(
                gender_var.get(),
                surname_entry.get(),
                name_entry.get(),
                patronymic_entry.get(),
                int(birth_entry.get()),
                sub_entry.get(),
                pos_entry.get(),
                start_entry.get()
            )
            self.show_result("Успех" if success else "Ошибка")
            if success:
                window.destroy()

        btn.config(command=submit)
        btn.pack(pady=10)

    def delete_worker_form(self):
        fields = ["Номер работника"]
        window, entries, btn = self.get_input("Удалить сотрудника", fields)

        def submit():
            success = self.controller.delete_worker(
                int(entries["Номер работника"].get())
            )
            self.show_result("Успех" if success else "Ошибка")
            if success:
                window.destroy()

        btn.config(command=submit)

    def list_by_age_gender_form(self):
        window = tk.Toplevel(self.root)
        window.title("Список по возрасту и полу")

        tk.Label(window, text="Возраст").pack()
        age_entry = tk.Entry(window)
        age_entry.pack()

        tk.Label(window, text="Пол").pack()
        gender_var = tk.StringVar()
        gender_combo = ttk.Combobox(window, textvariable=gender_var, values=['мужской', 'женский'])
        gender_combo.pack()

        btn = tk.Button(window, text="Выполнить")

        def submit():
            data = self.controller.list_workers_by_age_gender(
                int(age_entry.get()),
                gender_var.get()
            )
            columns = ["Номер", "Фамилия", "Имя", "Отчество", "Год", "Пол", "Должность"]
            self.show_list(data, columns)
            window.destroy()

        btn.config(command=submit)
        btn.pack(pady=10)

    def list_by_subdivision_form(self):
        fields = ["Подразделение"]
        window, entries, btn = self.get_input("Список по подразделению", fields)

        def submit():
            data = self.controller.list_workers_by_subdivision(
                entries["Подразделение"].get()
            )
            columns = ["Номер", "Фамилия", "Имя", "Отчество", "Год", "Пол", "Должность"]
            self.show_list(data, columns)
            window.destroy()

        btn.config(command=submit)

    def max_repair_sub(self):
        sub, count = self.controller.max_repair_subdivision()
        if sub is None:
            self.show_result("Нет данных")
        else:
            self.show_result(f"Подразделение: {sub}, Количество: {count}")

    def count_devices_form(self):
        fields = ["Подразделение", "Название устройства"]
        window, entries, btn = self.get_input("Количество техники за 3 года", fields)

        def submit():
            count = self.controller.count_devices_three_years(
                entries["Подразделение"].get(),
                entries["Название устройства"].get()
            )
            self.show_result(f"Количество: {count}")
            window.destroy()

        btn.config(command=submit)

    def add_work_log_form(self):
        fields = ["Номер работника", "Дата начала (YYYY-MM-DD HH:MM:SS)", "Дата окончания (YYYY-MM-DD HH:MM:SS)",
                  "Подразделение", "Должность"]
        window, entries, btn = self.get_input("Учёт работы", fields)

        def submit():
            success = self.controller.add_work_log(
                int(entries["Номер работника"].get()),
                entries["Дата начала (YYYY-MM-DD HH:MM:SS)"].get(),
                entries["Дата окончания (YYYY-MM-DD HH:MM:SS)"].get(),
                entries["Подразделение"].get(),
                entries["Должность"].get()
            )
            self.show_result("Успех" if success else "Ошибка")
            if success:
                window.destroy()

        btn.config(command=submit)

    def take_for_repair_form(self):
        window = tk.Toplevel(self.root)
        window.title("Принять в ремонт")

        tk.Label(window, text="Номер ремонтника").pack()
        repairer_entry = tk.Entry(window)
        repairer_entry.pack()

        tk.Label(window, text="Перечень деталей").pack()
        details_entry = tk.Entry(window)
        details_entry.pack()

        tk.Label(window, text="Дата (YYYY-MM-DD)").pack()
        date_entry = tk.Entry(window)
        date_entry.pack()

        tk.Label(window, text="Стоимость").pack()
        cost_entry = tk.Entry(window)
        cost_entry.pack()

        tk.Label(window, text="ID ремонта").pack()
        repair_id_entry = tk.Entry(window)
        repair_id_entry.pack()

        tk.Label(window, text="Вид ремонта").pack()
        type_var = tk.StringVar()
        type_combo = ttk.Combobox(window, textvariable=type_var,
                                  values=['Капитальный', 'Диагностика', 'Замена деталей', 'Профилактика'])
        type_combo.pack()

        btn = tk.Button(window, text="Выполнить")

        def submit():
            success = self.controller.take_for_repair(
                int(repairer_entry.get()),
                details_entry.get(),
                date_entry.get(),
                float(cost_entry.get()),
                int(repair_id_entry.get()),
                type_var.get()
            )
            self.show_result("Успех" if success else "Ошибка")
            if success:
                window.destroy()

        btn.config(command=submit)
        btn.pack(pady=10)

    def finish_repair_form(self):
        window = tk.Toplevel(self.root)
        window.title("Закончить ремонт")

        tk.Label(window, text="Дата (YYYY-MM-DD)").pack()
        date_entry = tk.Entry(window)
        date_entry.pack()

        tk.Label(window, text="Списание").pack()
        writeoff_var = tk.StringVar()
        writeoff_combo = ttk.Combobox(window, textvariable=writeoff_var, values=['0', '1'])
        writeoff_combo.pack()

        tk.Label(window, text="ID ремонта").pack()
        id_entry = tk.Entry(window)
        id_entry.pack()

        btn = tk.Button(window, text="Выполнить")

        def submit():
            success = self.controller.finish_repair(
                date_entry.get(),
                bool(int(writeoff_var.get())),
                int(id_entry.get())
            )
            self.show_result("Успех" if success else "Ошибка")
            if success:
                window.destroy()

        btn.config(command=submit)
        btn.pack(pady=10)


class Controller:
    def __init__(self, model, view):
        self.model = model
        self.view = view

    def add_device(self, inv_num, name, model, year, sub, date):
        return self.model.add_device(inv_num, name, model, year, sub, date)

    def edit_device(self, inv_num, field, value):
        return self.model.edit_device(inv_num, field, value)

    def move_device(self, inv_num, date, new_sub):
        return self.model.move_device(inv_num, date, new_sub)

    def send_to_repair(self, date, from_w, to_w, inv):
        return self.model.send_to_repair(date, from_w, to_w, inv)

    def edit_worker(self, w_num, field, value, date):
        return self.model.edit_worker(w_num, field, value, date)

    def add_worker(self, gender, surname, name, patronymic, birth_year, sub, pos, start_date):
        return self.model.add_worker(gender, surname, name, patronymic, birth_year, sub, pos, start_date)

    def delete_worker(self, w_num):
        return self.model.delete_worker(w_num)

    def list_workers_by_age_gender(self, age, gender):
        return self.model.list_workers_by_age_gender(age, gender)

    def list_workers_by_subdivision(self, sub):
        return self.model.list_workers_by_subdivision(sub)

    def max_repair_subdivision(self):
        return self.model.max_repair_subdivision()

    def count_devices_three_years(self, sub, dev):
        return self.model.count_devices_three_years(sub, dev)

    def add_work_log(self, w_num, start, end, sub, pos):
        return self.model.add_work_log(w_num, start, end, sub, pos)

    def take_for_repair(self, repairer, details, date, cost, repair_id, type_repair):
        return self.model.take_for_repair(repairer, details, date, cost, repair_id, type_repair)

    def finish_repair(self, date, writeoff, repair_id):
        return self.model.finish_repair_proc(date, writeoff, repair_id)


if __name__ == "__main__":
    root = tk.Tk()
    model = Database()
    view = View(root)
    controller = Controller(model, view)
    view.controller = controller  # To access controller from view
    root.mainloop()