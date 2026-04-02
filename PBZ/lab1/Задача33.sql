use lab1;
select DISTINCT Город from Поставщики_S
Union select Город from Детали_P
Union select Город from Проекты_J;