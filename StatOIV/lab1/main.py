import pandas as pd
import numpy as np
import	matplotlib.pyplot	as	plt
import	seaborn	as	sns

def studying_structure(df)->None:
    # Изучить	размерность	датасета	(количество	строк	и	столбцов)
    print(f"Размер	датасета:	{df.shape} \n")

    # Изучить типы каждого столбца
    print(f"Типы каждого столбца:\n{df.dtypes} \n")

    #Первые и последние строки данных
    print(f"Первые строки столбца:\n{df.head(8)}\n")
    print(f"Последние строки столбца:\n{df.tail(8)}\n")

    #Получить	общую	информацию	о	датасете	с	помощью	методов	info()	и  describe()
    print("Общая информация")
    print(df.info())
    print(df.describe())

def data_preprocessing(df)->object:
    #Поиск	пропусков
    print("Колво пропусков: \n", df.isnull().sum(), "\n")
    print("Колво пропусков в процентах: \n", df.isnull().sum() / len(df) * 100, "\n")

    #Обработка	пропусков
    df=df.dropna()  # удаление	строк	с	пропусками

    #Обработка дупликатов
    print("Дупликаты:", df[df.duplicated(subset=['Patient_ID'])])
    df=df.drop_duplicates()

    # Обработка выбросов по Heart_rate
    #	Метод	межквартильного	размаха	(IQR)
    Q1 = df['Heart_Rate'].quantile(0.25)
    Q3 = df['Heart_Rate'].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    #Выводим все выбросы
    print("Выбросы: \n", df[(df['Heart_Rate'] < lower_bound) & (df['Heart_Rate'] > upper_bound)] )
    #Удаляем их
    df = df[(df['Heart_Rate'] >= lower_bound) & (df['Heart_Rate'] <= upper_bound)]

    #Преобразование некоторых столбцы в категориальные переменные
    df['Risk_Level'] = df['Risk_Level'].astype('category')
    df['On_Oxygen'] = df['On_Oxygen'].astype('category')
    df['Consciousness'] = df['Consciousness'].astype('category')
    return df

def question_answers(df)->None:
    print("1. Есть ли связь между частотой сердцебиения и систолическим артериальным давлением")
    corr = df[["Heart_Rate", "Systolic_BP"]].corr().iloc[0, 1]
    t=np.sqrt(corr*corr*998/1-corr*corr)
    if t<0.05:
        print("Корреляция не наблюдается")
    else:
        if corr>0:
            print("Наблюдается прямая зависимость между частотой сердцебиения и систолическим артериальным давлением, коэфициент Пирсона равен", corr)
        else:
            print("Наблюдается обратная зависимость между частотой сердцебиения и систолическим артериальным давлением, коэфициент Пирсона равен", corr)

    print("2. В какой зоне риска наибольшее количество людей")
    counts = df['Risk_Level'].value_counts()
    max_count = counts.max()
    rows_with_max = df['Risk_Level'].isin(counts[counts == max_count].index).sum()
    most_frequent_categories = counts[counts == max_count].index.tolist()
    print("Наиболее часто встречающаяся зона риска:", most_frequent_categories)
    print("Количество людей в ней:", rows_with_max)

    print("3.Как температура тела связана с частотой дыхания?")
    corr = df[["Respiratory_Rate", "Temperature"]].corr().iloc[0, 1]
    t = np.sqrt(corr * corr * 998 / 1 - corr * corr)
    if t < 0.05:
        print("Корреляция не наблюдается")
    else:
        if corr > 0:
            print(
                "Наблюдается прямая зависимость между частотой сердцебиения и температурой, коэфициент Пирсона равен",corr)
        else:
            print(
                "Наблюдается обратная зависимость между частотой сердцебиения и температурой, коэфициент Пирсона равен",corr)

    print("\n4. Есть ли различия в температуре тела между пациентами с разным уровнем риска?")

    # Группируем по уровню риска и вычисляем среднюю температуру
    avg_temp_by_risk = df.groupby('Risk_Level', observed=False)['Temperature'].mean().sort_values(ascending=False)

    print("Средняя температура по группам риска:")
    for risk_level, avg_temp in avg_temp_by_risk.items():
        print(f"{risk_level}: {avg_temp:.2f}°C")

    # Определяем группу с наибольшей средней температурой
    highest_risk_group = avg_temp_by_risk.index[0]
    highest_temp = avg_temp_by_risk.iloc[0]

    print(f"\nНаибольшая средняя температура ({highest_temp:.2f}°C) наблюдается у пациентов с уровнем риска: {highest_risk_group}")

    print("\n5. У кого выше насыщение кислородом: у людей на кислородном обеспечении или без него")

    # Группируем по использованию кислорода и вычисляем среднюю сатурацию
    avg_saturation_by_oxygen = df.groupby('On_Oxygen', observed=False)['Oxygen_Saturation'].mean()

    print("Средний уровень насыщения кислородом:")
    print(f"Пациенты без обеспечения кислородрм: {avg_saturation_by_oxygen.loc[0]:.2f}%")
    print(f"Пациенты с обеспечением кислородом: {avg_saturation_by_oxygen.loc[1]:.2f}%")

    # Сравниваем значения
    if avg_saturation_by_oxygen.loc[0] > avg_saturation_by_oxygen.loc[1]:
        print("Выше у пациентов без кислородной поддержки")
    elif avg_saturation_by_oxygen.loc[0] < avg_saturation_by_oxygen.loc[1]:
        print("Выше у пациентов c кислородной поддержкой")

    print("\n6. Есть ли связь между частотой сердцебиения и частотой дыхания")
    corr = df[["Respiratory_Rate", "Heart_Rate"]].corr().iloc[0, 1]
    t = np.sqrt(corr * corr * 998 / 1 - corr * corr)
    if t < 0.05:
        print("Корреляция не наблюдается")
    else:
        if corr > 0:
            print(
                "Наблюдается прямая зависимость между частотой сердцебиения и частотой дыхания, коэфициент Пирсона равен",
                corr)
        else:
            print(
                "Наблюдается обратная зависимость между частотой сердцебиения и частотой дыхания, коэфициент Пирсона равен",
                corr)

    print("\n7. Какой уровень сознания наиболее часто встречается?")

    # Подсчитываем частоту каждого уровня сознания
    consciousness_counts = df['Consciousness'].value_counts()

    print("Частота встречаемости уровней сознания:")
    for level, count in consciousness_counts.items():
        print(f"{level}: {count} пациентов")

    # Определяем наиболее часто встречающийся уровень сознания
    most_common_level = consciousness_counts.index[0]
    most_common_count = consciousness_counts.iloc[0]

    print(f"\nНаиболее часто встречается уровень сознания: '{most_common_level}' ({most_common_count} пациентов)")

    print("\n8. Есть ли различия в частоте сердцебиения среди пациентов с разным уровнем риска?")

    # Группируем по уровню риска и вычисляем среднюю температуру
    avg_rate_by_risk = df.groupby('Risk_Level', observed=False)['Heart_Rate'].mean().sort_values(ascending=False)

    print("Средняя частота сердцебиения по группам риска:")
    for risk_level, avg_rate in avg_rate_by_risk.items():
        print(f"{risk_level}: {avg_rate:.2f}")

    # Определяем группу с наибольшей средней температурой
    highest_risk_group = avg_rate_by_risk.index[0]
    highest_rate = avg_rate_by_risk.iloc[0]

    print(
        f"\nНаибольшая средняя частота сердцебиения ({highest_rate:.2f}) наблюдается у пациентов с уровнем риска: {highest_risk_group}")

    print("9. Есть ли связь между частотой дыхания и насыщением кислородом")
    corr = df[["Respiratory_Rate", "Oxygen_Saturation"]].corr().iloc[0, 1]
    t = np.sqrt(corr * corr * 998 / 1 - corr * corr)
    if t < 0.05:
        print("Корреляция не наблюдается")
    else:
        if corr > 0:
            print(
                "Наблюдается прямая зависимость между частотой дыхания и насыщением кислородом, коэфициент Пирсона равен",
                corr)
        else:
            print(
                "Наблюдается обратная зависимость частотой дыхания и насыщением кислородом, коэфициент Пирсона равен",
                corr)

    print("\n10. Как часто у пациентов с высоким риском наблюдается низкое насыщение кислородом (<90%)?")

    # Фильтруем пациентов с высоким риском
    high_risk_patients = df[df['Risk_Level'] == 'High']
    print(high_risk_patients)

    # Подсчитываем пациентов с низким насыщением кислорода (<90%)
    low_saturation_count = high_risk_patients[high_risk_patients['Oxygen_Saturation'] < 90].shape[0]

    # Общее количество пациентов с высоким риском
    total_high_risk = high_risk_patients.shape[0]

    # Вычисляем процент
    percentage = (low_saturation_count / total_high_risk) * 100 if total_high_risk > 0 else 0

    print(f"Из {total_high_risk} пациентов с высоким риском:")
    print(f"- {low_saturation_count} имеют насыщение кислородом <90%")
    print(f"- Это составляет {percentage:.2f}% от всех пациентов с высоким риском")

def onedimensional_visualization(df)->None:
    #Гистограмма частоты распределения частоты сердцебиения
    plt.figure(figsize=(10, 6))
    plt.hist(df['Heart_Rate'], bins=30, alpha=0.7, edgecolor='black')
    plt.title('Распределение частоты сердцебиения')
    plt.xlabel('Частота сердцебиения')
    plt.ylabel('Частота')
    plt.grid(True, alpha=0.3)
    plt.show()
    # Гистограмма частоты распределения температуры
    plt.figure(figsize=(10, 6))
    plt.hist(df['Temperature'], bins=30, alpha=0.7, edgecolor='black')
    plt.title('Температуры')
    plt.xlabel('Температуры')
    plt.ylabel('Частота')
    plt.grid(True, alpha=0.3)
    plt.show()
    # Box	plot для частоты дыхания
    plt.figure(figsize=(8, 6))
    plt.boxplot(df['Respiratory_Rate'])
    plt.title('Коробчатая диаграмма частоты дыхания')
    plt.ylabel('Частота дыхания')
    plt.show()
    # Box	plot для систолического артериального давления
    plt.figure(figsize=(8, 6))
    plt.boxplot(df['Systolic_BP'])
    plt.title('Коробчатая диаграмма систолического артериального давления')
    plt.ylabel('Систолическое артериальное давление')
    plt.show()
    #Простая солбчатая диаграмма(Bar plot) для уровней риска
    plt.figure(figsize=(10, 6))
    df['Risk_Level'].value_counts().plot(kind='bar')
    plt.title('Распределение по категориям')
    plt.xlabel('Категория')
    plt.ylabel('Количество')
    plt.xticks(rotation=45)
    plt.show()
    # Простая солбчатая диаграмма(Bar plot) для видов сознания
    plt.figure(figsize=(10, 6))
    df['Consciousness'].value_counts().plot(kind='bar')
    plt.title('Распределение по категориям')
    plt.xlabel('Категория')
    plt.ylabel('Количество')
    plt.xticks(rotation=45)
    plt.show()

def multidimensional_visualization(df)->None:
    # Correlation matrix для количественных переменных
    corr_matrix = df.select_dtypes(include=[np.number]).corr()
    #	Тепловая	карта	корреляций
    plt.figure(figsize=(12, 8))
    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0, square=True, fmt='.2f', cbar_kws={'label': 'Коэффициенткорреляции'})
    plt.title('Матрица	корреляций')
    mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
    plt.figure(figsize=(12, 8))
    sns.heatmap(corr_matrix, mask=mask, annot=True, cmap='coolwarm', center=0)
    plt.title('Матрица корреляций (нижний треугольник)')
    plt.show()
    #	Простая диаграмма рассеяния между температурой и частотой сердцебиения
    plt.figure(figsize=(10, 6))
    plt.scatter(df['Temperature'], df['Heart_Rate'], alpha=0.6)
    plt.xlabel('Температура')
    plt.ylabel('Частота сердцебиения')
    plt.title('Зависимость температуры от частоты сердцебиения')
    plt.show()
    #	Простая диаграмма рассеяния между температурой и частотой дыхания
    plt.figure(figsize=(10, 6))
    plt.scatter(df['Temperature'], df['Respiratory_Rate'], alpha=0.6)
    plt.xlabel('Температура')
    plt.ylabel('Частота дыхания')
    plt.title('Зависимость температуры от частоты дыхания')
    plt.show()
    # 1) Таблица сопряжённости (абсолютные частоты)
    contingency_table = pd.crosstab(df['Risk_Level'], df['Consciousness'])
    print("Таблица сопряжённости (абсолютные частоты):")
    print(contingency_table)

    plt.figure(figsize=(10, 6))
    sns.heatmap(contingency_table, annot=True, fmt='d', cmap='Blues')
    plt.title('Тепловая карта таблицы сопряженности')
    plt.show()


plt.style.use('seaborn-v0_8')
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['font.size'] = 12

# Настройка отображения всех столбц""ов
pd.set_option("display.max_columns", None)

# Если нужно и все строки
pd.set_option("display.max_rows", None)

# Выбор	и	загрузка	данных
df = pd.read_csv('Health_Risk_Dataset.csv')
studying_structure(df)

#onedimensional_visualization(df)

print(df.iloc[[1,2,5,10]])

#multidimensional_visualization(df)

# Предобработка	данных
#df=data_preprocessing(df)

#question_answers(df)

