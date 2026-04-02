DROP function IF EXISTS `count_devices_in_subdivision_year`;
DROP function IF EXISTS `count_sent_to_repair`;
DROP TRIGGER IF EXISTS `trg_invoice_tag`;
DROP PROCEDURE IF EXISTS `send_it_to_repairs`;
DROP PROCEDURE IF EXISTS `take_it_for_repair`;
DROP PROCEDURE IF EXISTS `finish_repair`;

# Функция, счиающая количество техники определенного наименовая в определенном подразделении, которая была там хотя бы единожды за год
DELIMITER $$

CREATE FUNCTION `count_devices_in_subdivision_year`(
  p_sub_name VARCHAR(255),
  p_dev_name VARCHAR(255),
  p_year INT
) RETURNS INT
DETERMINISTIC
READS SQL DATA
BEGIN
  DECLARE v_count INT DEFAULT 0;
  DECLARE v_start_date DATE;
  DECLARE v_end_date DATE;

  -- Построим даты корректно
  SET v_start_date = MAKEDATE(p_year, 1); -- yyyy-01-01
  SET v_end_date   = DATE_SUB(DATE_ADD(v_start_date, INTERVAL 1 YEAR), INTERVAL 1 DAY); -- yyyy-12-31

  SELECT COUNT(DISTINCT m.`Инвентарный_номер`) INTO v_count
  FROM `Перемещение_устройства` m
  JOIN `Подразделение` s ON m.`ID_Подразделения` = s.`ID_Подразделения`
  JOIN `Устройство` u ON u.`Инвентарный_номер` = m.`Инвентарный_номер`
  WHERE u.`Название_устройства` = p_dev_name
    AND s.`Название_подразделения` = p_sub_name
    -- начало перемещения не позднее конца года
    AND m.`Дата_перемещения` <= v_end_date;

  RETURN v_count;
END$$

# Триггер, который пересчитывает финальную стоимость накладной с учётом налога

CREATE TRIGGER `trg_invoice_tag`
BEFORE INSERT ON `Накладная`
FOR EACH ROW
BEGIN
  SET NEW.`Стоимость_на_текущую_дату` = ROUND(NEW.`Стоимость_на_текущую_дату` * 1.15, 2);
END$$

# Функция, подсчитывающая количество техники, которую передало в ремонт подразделение
CREATE FUNCTION count_sent_to_repair(p_subdivision VARCHAR(100))
RETURNS INT
NOT DETERMINISTIC
READS SQL DATA
BEGIN
  DECLARE v_count INT DEFAULT 0;

  SELECT COUNT(*) INTO v_count
  FROM `Перемещение_устройства` m
  JOIN `Подразделение` s ON m.`ID_Подразделения` = s.`ID_Подразделения`
  WHERE s.`Название_подразделения` = 'Ремонт'
    AND EXISTS (
      SELECT 1
      FROM `Перемещение_устройства` m_prev
      JOIN `Подразделение` s_prev ON m_prev.`ID_Подразделения` = s_prev.`ID_Подразделения`
      WHERE m_prev.`Инвентарный_номер` = m.`Инвентарный_номер`
        -- требуем, что m_prev — ближайший предыдущий по (Дата_перемещения, ID_Перемещения)
        AND (m_prev.`Дата_перемещения`, m_prev.`ID_Перемещения`) =
            (
              SELECT MAX(m2.`Дата_перемещения`), MAX(m2.`ID_Перемещения`)
              FROM `Перемещение_устройства` m2
              WHERE m2.`Инвентарный_номер` = m.`Инвентарный_номер`
                AND (m2.`Дата_перемещения` < m.`Дата_перемещения`
                     OR (m2.`Дата_перемещения` = m.`Дата_перемещения` AND m2.`ID_Перемещения` < m.`ID_Перемещения`))
            )
        AND s_prev.`Название_подразделения` = p_sub_name
  );

  RETURN v_count;
END$$

# Процедура, которая отвечает за отправление в ремонт устройства
CREATE PROCEDURE `send_it_to_repairs`(
  IN p_date DATE,
  IN p_from_worker BIGINT UNSIGNED,
  IN p_to_worker BIGINT UNSIGNED,
  IN p_inv_number BIGINT UNSIGNED
)
BEGIN
  DECLARE v_exists INT DEFAULT 0;
  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    ROLLBACK;
    RESIGNAL;
  END;
  START TRANSACTION;
    SELECT COUNT(*) INTO v_exists
    FROM `Устройство`
    WHERE `Инвентарный_номер` = p_inv_number;
    IF v_exists = 0 THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Устройство с указанным инвентарным номером не найдено';
    END IF;
    SELECT COUNT(*) INTO v_exists
    FROM `Работник`
    WHERE `Номер_работника` = p_from_worker;
    IF v_exists = 0 THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Работник (сдавший) не найден';
    END IF;
    SELECT COUNT(*) INTO v_exists
    FROM `Работник`
    WHERE `Номер_работника` = p_to_worker;
    IF v_exists = 0 THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Работник (принявший) не найден';
    END IF;
    INSERT INTO `Ремонт` (
      `Номер_накладной`,
      `Вид_ремонта`,
      `Срок_ремонта`,
      `Инвентарный_номер`,
      `Номер_сдавшего_работника`,
      `Номер_принявшего_работника`,
      `Номер_ремонтника`
    ) VALUES (
      NULL,
      NULL,
      NULL,
      p_inv_number,
      p_from_worker,
      p_to_worker,
      NULL
    );
    INSERT INTO `Перемещение_устройства` (
      `Инвентарный_номер`,
      `Дата_перемещения`,
      `ID_Подразделения`
    ) VALUES (
      p_inv_number,
      p_date,
      1  
    );
  COMMIT;
END$$

#Процедура, отвечающая за прием в ремонт устройства

CREATE PROCEDURE `take_it_for_repair`(
  IN p_repairer    BIGINT UNSIGNED,
  IN p_details     VARCHAR(1000),
  IN p_date        DATE,
  IN p_cost        DECIMAL(14,2),
  IN p_repair_id   BIGINT UNSIGNED
)
BEGIN
  DECLARE v_exists INT DEFAULT 0;
  DECLARE v_new_invoice_id BIGINT UNSIGNED DEFAULT NULL;
  DECLARE v_existing_invoice BIGINT UNSIGNED DEFAULT NULL;

  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    ROLLBACK;
    RESIGNAL;
  END;

  START TRANSACTION;

    SELECT COUNT(*) INTO v_exists
    FROM `Работник`
    WHERE `Номер_работника` = p_repairer;
    IF v_exists = 0 THEN
      SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'Такого ремонтника нет';
    END IF;

    SELECT COUNT(*) INTO v_exists
    FROM `Ремонт`
    WHERE `ID_Ремонта` = p_repair_id;
    IF v_exists = 0 THEN
      SIGNAL SQLSTATE '45000'
         SET MESSAGE_TEXT = 'Не существует ремонта с таким ID';
    END IF;

    SELECT `Номер_накладной` INTO v_existing_invoice
    FROM `Ремонт`
    WHERE `ID_Ремонта` = p_repair_id
    LIMIT 1;

    IF v_existing_invoice IS NOT NULL THEN
      SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Существует накладная в ремонте';
    END IF;

    INSERT INTO `Накладная` (`Перечень_деталей`, `Стоимость_на_текущую_дату`, `Дата`)
    VALUES (p_details, p_cost, p_date);

    SET v_new_invoice_id = LAST_INSERT_ID();

    UPDATE `Ремонт`
    SET
      `Номер_накладной` = v_new_invoice_id,
      `Номер_ремонтника` = p_repairer
    WHERE `ID_Ремонта` = p_repair_id;

  COMMIT;
END$$

CREATE PROCEDURE `finish_repair`(
  IN p_date DATE,
  IN p_writeoff BOOL,
  IN p_repair_id BIGINT UNSIGNED
)
BEGIN
  DECLARE v_inv BIGINT UNSIGNED DEFAULT NULL;
  DECLARE v_move_id BIGINT UNSIGNED DEFAULT NULL;
  DECLARE v_move_date DATE DEFAULT NULL;
  DECLARE v_prev_subdivision_id BIGINT UNSIGNED DEFAULT NULL;
  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    ROLLBACK;
    RESIGNAL;
  END;
  START TRANSACTION;
    SELECT `Инвентарный_номер` INTO v_inv
    FROM `Ремонт`
    WHERE `ID_Ремонта` = p_repair_id
    LIMIT 1;
    IF v_inv IS NULL THEN
      SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Запись ремонта не найдена';
    END IF;
    IF p_writeoff THEN
      UPDATE `Устройство`
      SET `Списание` = 1
      WHERE `Инвентарный_номер` = v_inv;
      IF ROW_COUNT() = 0 THEN
        SIGNAL SQLSTATE '45000'
          SET MESSAGE_TEXT = 'Устройство для списания не найдено';
      END IF;
      -- Нет вставки перемещения для списания, так как нет подразделения 'Списание'
    ELSE
      SELECT `ID_Перемещения`, `Дата_перемещения`
      INTO v_move_id, v_move_date
      FROM `Перемещение_устройства`
      WHERE `Инвентарный_номер` = v_inv
        AND `ID_Подразделения` = 1  -- 'Ремонт'
      ORDER BY `Дата_перемещения` DESC, `ID_Перемещения` DESC
      LIMIT 1;
      IF v_move_id IS NULL THEN
        SIGNAL SQLSTATE '45000'
          SET MESSAGE_TEXT = 'Запись о приёме в ремонт не найдена';
      END IF;
      SELECT `ID_Подразделения` INTO v_prev_subdivision_id
      FROM `Перемещение_устройства`
      WHERE `Инвентарный_номер` = v_inv
        AND (
          (`Дата_перемещения` < v_move_date)
          OR (`Дата_перемещения` = v_move_date AND `ID_Перемещения` < v_move_id)
        )
      ORDER BY `Дата_перемещения` DESC, `ID_Перемещения` DESC
      LIMIT 1;
      IF v_prev_subdivision_id IS NULL THEN
        SIGNAL SQLSTATE '45000'
          SET MESSAGE_TEXT = 'Подразделение-источник не найдено';
      END IF;
      INSERT INTO `Перемещение_устройства` (
        `Инвентарный_номер`,
        `Дата_перемещения`,
        `ID_Подразделения`
      ) VALUES (
        v_inv,
        p_date,
        v_prev_subdivision_id
      );
    END IF;
  COMMIT;
END$$

DELIMITER ;
