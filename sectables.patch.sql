CREATE TABLE orderperformers
(
  order_id integer NOT NULL,
  person_id integer NOT NULL,
  CONSTRAINT orderperformers_pkey PRIMARY KEY (order_id, person_id),
  CONSTRAINT orderperformers_order_id_fkey FOREIGN KEY (order_id)
      REFERENCES orders (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION,
  CONSTRAINT orderperformers_person_id_fkey FOREIGN KEY (person_id)
      REFERENCES people (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION
)
WITH (
  OIDS=FALSE
);
ALTER TABLE orderperformers OWNER TO orderman;

CREATE TABLE ordercustomers
(
  order_id integer NOT NULL,
  person_id integer NOT NULL,
  CONSTRAINT ordercustomers_pkey PRIMARY KEY (order_id, person_id),
  CONSTRAINT ordercustomers_order_id_fkey FOREIGN KEY (order_id)
      REFERENCES orders (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION,
  CONSTRAINT ordercustomers_person_id_fkey FOREIGN KEY (person_id)
      REFERENCES people (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION
)
WITH (
  OIDS=FALSE
);
ALTER TABLE ordercustomers OWNER TO orderman;

-- Sanitize table actionperformers by deleting unnecessary columns
ALTER TABLE actionperformers DROP CONSTRAINT actionperformers_pkey;
ALTER TABLE actionperformers DROP COLUMN id;
ALTER TABLE actionperformers ADD CONSTRAINT actionperformers_pkey PRIMARY KEY (action_id, person_id);

-- Sanitize table actionperformers by deleting unnecessary columns
ALTER TABLE orderinventories DROP CONSTRAINT orderinventories_pkey;
ALTER TABLE orderinventories DROP COLUMN id;
ALTER TABLE orderinventories ADD CONSTRAINT orderinventories_pkey PRIMARY KEY (order_id, inv_id);

