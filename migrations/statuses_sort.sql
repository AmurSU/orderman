ALTER TABLE statuses ADD COLUMN gui_priority integer;

UPDATE statuses SET gui_priority = 1 WHERE id = 3;
UPDATE statuses SET gui_priority = 10 WHERE id = 7;
UPDATE statuses SET gui_priority = 20 WHERE id = 8;
UPDATE statuses SET gui_priority = 21 WHERE id = 9;
UPDATE statuses SET gui_priority = 22 WHERE id = 10;
UPDATE statuses SET gui_priority = 23 WHERE id = 13;
UPDATE statuses SET gui_priority = 30 WHERE id = 5;
