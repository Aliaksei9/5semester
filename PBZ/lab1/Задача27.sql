use lab1;
SELECT DISTINCT ks.П
FROM Количество_деталей_S ks
WHERE ks.Д = 'Д1'
  AND ks.S > (
      SELECT AVG(ks2.S)
      FROM Количество_деталей_S ks2
      WHERE ks2.Д = 'Д1'
        AND ks2.ПР = ks.ПР
  );
