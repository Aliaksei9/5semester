CREATE DATABASE IF NOT EXISTS lab2;
USE lab2;
DROP TABLE IF EXISTS `Перемещение_устройства`;
DROP TABLE IF EXISTS `Учёт_работы`;
DROP TABLE IF EXISTS `Ремонт`;
DROP TABLE IF EXISTS `Накладная`;
DROP TABLE IF EXISTS `Устройство`;
DROP TABLE IF EXISTS `Работник`;
DROP TABLE IF EXISTS `Подразделение`;

CREATE TABLE `Подразделение` (
	`ID_Подразделения` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `Название_подразделения` VARCHAR(255) NOT NULL,
     PRIMARY KEY (`ID_Подразделения`)
);

CREATE TABLE `Работник` (
  `Номер_работника` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `Фамилия` VARCHAR(150) NOT NULL,
  `Имя` VARCHAR(150) NOT NULL,
  `Отчество` VARCHAR(150) NOT NULL,
  `Год_рождения` INT NOT NULL,
  `Пол` BOOL NOT NULL, 
  `Должность` VARCHAR(200) NOT NULL,
  PRIMARY KEY (`Номер_работника`)
);

CREATE TABLE `Устройство` (
  `Инвентарный_номер` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `Название_устройства` VARCHAR(255) NOT NULL,
  `Модель` VARCHAR(200) NOT NULL,
  `Год_выпуска` INT NOT NULL,
  `Списание` BOOL NOT NULL,
  PRIMARY KEY (`Инвентарный_номер`)
);

CREATE TABLE `Перемещение_устройства` (
  `ID_Перемещения` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `Инвентарный_номер` BIGINT UNSIGNED NOT NULL,
  `Дата_перемещения` DATE NOT NULL,
  `ID_Подразделения` BIGINT UNSIGNED NOT NULL,
  PRIMARY KEY (`ID_Перемещения`),
  CONSTRAINT `fk_move_device`
    FOREIGN KEY (`Инвентарный_номер`) REFERENCES `Устройство`(`Инвентарный_номер`)
    ON UPDATE CASCADE 
    ON DELETE RESTRICT,
 CONSTRAINT `fk_move_subdivision`
    FOREIGN KEY (`ID_Подразделения`) REFERENCES `Подразделение`(`ID_Подразделения`)
    ON UPDATE CASCADE 
    ON DELETE RESTRICT
);

CREATE TABLE `Учёт_работы` (
  `ID_учёта` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `Номер_работника` BIGINT UNSIGNED NOT NULL,
  `Дата_начала_работы` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `Дата_окончания_работы` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `ID_Подразделения` BIGINT UNSIGNED NOT NULL,
  `Должность` VARCHAR(200) NOT NULL,
  PRIMARY KEY (`ID_учёта`),
  CONSTRAINT `fk_worklog_worker`
    FOREIGN KEY (`Номер_работника`) REFERENCES `Работник` (`Номер_работника`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_worklog_subdivision`
    FOREIGN KEY (`ID_Подразделения`) REFERENCES `Подразделение`(`ID_Подразделения`)
    ON UPDATE CASCADE 
    ON DELETE RESTRICT
);

CREATE TABLE `Накладная` (
  `Номер_накладной` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `Перечень_деталей` VARCHAR(1000) DEFAULT NULL,
  `Стоимость_на_текущую_дату` DECIMAL(14,2) DEFAULT 0.00,
  `Дата` DATE NOT NULL,
  PRIMARY KEY (`Номер_накладной`)
);
CREATE TABLE `Ремонт` (
  `ID_Ремонта` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `Номер_накладной` BIGINT UNSIGNED default NULL,
  `Вид_ремонта` VARCHAR(255) DEFAULT NULL,
  `Срок_ремонта` VARCHAR(100) DEFAULT NULL,
  `Инвентарный_номер` BIGINT UNSIGNED NOT NULL,
  `Номер_сдавшего_работника` BIGINT UNSIGNED,
  `Номер_принявшего_работника` BIGINT UNSIGNED,
  `Номер_ремонтника` BIGINT UNSIGNED,
  PRIMARY KEY (`ID_Ремонта`),
  CONSTRAINT `fk_repair_device`
    FOREIGN KEY (`Инвентарный_номер`) REFERENCES `Устройство` (`Инвентарный_номер`)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_repair_invoice`
    FOREIGN KEY (`Номер_накладной`) REFERENCES `Накладная` (`Номер_накладной`)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_repair_worker_from`
    FOREIGN KEY (`Номер_сдавшего_работника`) REFERENCES `Работник` (`Номер_работника`)
    ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_repair_worker_received`
    FOREIGN KEY (`Номер_принявшего_работника`) REFERENCES `Работник` (`Номер_работника`)
    ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_repair_worker_repairer`
    FOREIGN KEY (`Номер_ремонтника`) REFERENCES `Работник` (`Номер_работника`)
    ON DELETE SET NULL ON UPDATE CASCADE
);

-- Подразделения (обязательно есть "Ремонт")
INSERT INTO `Подразделение` (`ID_Подразделения`, `Название_подразделения`) VALUES
(1, 'Ремонт'),
(2, 'Отдел поставок'),
(3, 'IT'),
(4, 'Бухгалтерия'),
(5, 'Склад');

-- Работники (Пол: 1 = мужской, 0 = женский)
INSERT INTO `Работник` (`Номер_работника`, `Фамилия`, `Имя`, `Отчество`, `Год_рождения`, `Пол`, `Должность`) VALUES
(1, 'Иванов',   'Иван',  'Иванович',   1980, 1, 'Начальник отдела'),
(2, 'Петров',   'Пётр',  'Александрович',1990, 1, 'Инженер'),
(3, 'Сидорова', 'Анна',  'Петровна',   1985, 0, 'Специалист по приёму'),
(4, 'Кузнецов', 'Алексей','Михайлович', 1975, 1, 'Бухгалтер'),
(5, 'Морозова', 'Елена', 'Сергеевна',  1992, 0, 'Кладовщик'),
(6, 'Семенов',  'Дмитрий','Викторович', 1988, 1, 'Системный администратор'),
(7, 'Новикова', 'Ольга', 'Игоревна',   1983, 0, 'Ремонтник'),
(8, 'Фролов',   'Михаил','Денисович',  1995, 1, 'Техник');

-- Устройства
INSERT INTO `Устройство` (`Инвентарный_номер`, `Название_устройства`, `Модель`, `Год_выпуска`, `Списание`) VALUES
(1, 'Принтер',       'HP LaserJet Pro M404dn', 2019, 0),
(2, 'Монитор',       'Dell P2419H',            2018, 0),
(3, 'Сервер',        'HPE ProLiant DL380',     2017, 0),
(4, 'Ноутбук',       'Lenovo ThinkPad T480',   2020, 0),
(5, 'МФУ',           'Canon MF642C',           2016, 0),
(6, 'Маршрутизатор', 'Cisco ISR 4331',         2012, 1); 

-- Перемещения устройств (ссылки на существующие подразделения и устройства)
INSERT INTO `Перемещение_устройства` (`ID_Перемещения`, `Инвентарный_номер`, `Дата_перемещения`, `ID_Подразделения`) VALUES
(1, 1, '2022-03-15', 3), -- принтер в IT
(2, 2, '2023-01-02', 3), -- монитор в IT
(3, 3, '2023-01-05', 3), -- сервер в IT
(4, 4, '2024-03-05', 2), -- ноутбук в отдел поставок
(5, 5, '2024-06-20', 1), -- МФУ в Ремонт
(6, 6, '2025-02-28', 1); -- маршрутизатор в Ремонт

-- Учёт работы (записи о трудовой деятельности в подразделениях)
INSERT INTO `Учёт_работы` (`ID_учёта`, `Номер_работника`, `Дата_начала_работы`, `Дата_окончания_работы`, `ID_Подразделения`, `Должность`) VALUES
(1, 1, '2020-01-01 09:00:00', '2020-01-01 18:00:00', 3, 'Начальник отдела'),
(2, 2, '2021-05-10 08:30:00', '2021-05-10 09:30:00', 1, 'Инженер'),
(3, 3, '2023-05-10 08:30:00', '2023-05-10 10:30:00', 1, 'Специалист по приёму'),
(4, 4, '2023-08-15 09:00:00', '2023-08-15 23:00:00', 4, 'Бухгалтер'),
(5, 6, '2024-07-01 10:00:00', '2024-07-01 22:00:00', 3, 'Системный администратор');

-- Накладные
INSERT INTO `Накладная` (`Номер_накладной`, `Перечень_деталей`, `Стоимость_на_текущую_дату`, `Дата`) VALUES
(1, 'Картриджи; Плата питания',       12000.00, '2024-06-15'),
(2, 'Материнская плата; Жёсткий диск', 45000.00, '2023-11-20'),
(3, 'Блок питания',                     8000.00, '2025-01-10');

-- Ремонты (ссылки на устройства, накладные и работников)
INSERT INTO `Ремонт` (`ID_Ремонта`, `Номер_накладной`, `Вид_ремонта`, `Срок_ремонта`, `Инвентарный_номер`, `Номер_сдавшего_работника`, `Номер_принявшего_работника`, `Номер_ремонтника`) VALUES
(1, 1, 'Капитальный',    '14 дней', 1, 2, 3, 7), -- принтер: сдавал Петров (2), принял Сидорова (3), ремонтник Новикова (7)
(2, 2, 'Текущий',        '3 дня',   5, 5, 3, 7), -- МФУ
(3, 3, 'Замена детали',  '7 дней',  6, 2, 3, 7); -- маршрутизатор (списан), другой ремонтник
