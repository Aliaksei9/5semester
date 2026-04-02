use lab1;
select ПР from Проекты_J
where Город=(select min(Город) from Проекты_J);