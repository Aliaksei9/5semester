use lab1;
select П, Д, ПР from Поставщики_S as S, Детали_P as P, Проекты_J as J
where S.Город=P.Город and S.Город=J.Город and P.Город=J.Город;