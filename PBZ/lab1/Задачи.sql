use lab1;
#Задача 6
select П, Д, ПР from Поставщики_S as S, Детали_P as P, Проекты_J as J
where S.Город=P.Город and S.Город=J.Город and P.Город=J.Город;
#Задача 10
select Д from Количество_деталей_S, Поставщики_S, Проекты_J
where Количество_деталей_S.П=Поставщики_S.П and Количество_деталей_S.ПР=Проекты_J.ПР and Поставщики_S.Город='Лондон' and Проекты_J.Город='Лондон';
#Задача 9
select Д from Количество_деталей_S, Поставщики_S
where Количество_деталей_S.П=Поставщики_S.П and Поставщики_S.Город='Лондон';
#Задача 25
select ПР from Проекты_J
where Город=(select min(Город) from Проекты_J);
#Задача 30
select Д from Количество_деталей_S,  Проекты_J
where Количество_деталей_S.ПР=Проекты_J.ПР and Проекты_J.Город='Лондон';
#Задача 27
SELECT DISTINCT ks.П
FROM Количество_деталей_S ks
WHERE ks.Д = 'Д1'
  AND ks.S > (
      SELECT AVG(ks2.S)
      FROM Количество_деталей_S ks2
      WHERE ks2.Д = 'Д1'
        AND ks2.ПР = ks.ПР
  );
#Задача 12
SELECT ks.Д
FROM Количество_деталей_S ks
JOIN Поставщики_S ps ON ks.П = ps.П
JOIN Проекты_J pj ON ks.ПР = pj.ПР
WHERE ps.Город = pj.Город
GROUP BY ks.Д
HAVING COUNT(DISTINCT pj.ПР) = (
    SELECT COUNT(DISTINCT pj2.ПР)
    FROM Проекты_J pj2
    JOIN Поставщики_S ps2 ON ps2.Город = pj2.Город
);
#Задача 20
select DISTINCT Детали_P.Цвет from Количество_деталей_S, Детали_P
where Количество_деталей_S.П='П1' and Количество_деталей_S.Д=Детали_P.Д;
#Задача 33
select DISTINCT Город from Поставщики_S
Union select Город from Детали_P
Union select Город from Проекты_J;