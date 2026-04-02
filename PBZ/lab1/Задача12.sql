use lab1;
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
