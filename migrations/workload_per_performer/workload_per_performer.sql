ALTER TABLE orderperformers  ADD COLUMN workload numeric(5,2) DEFAULT 0.0;
ALTER TABLE orderperformers  ADD COLUMN current boolean DEFAULT false;
ALTER TABLE actionperformers ADD COLUMN workload numeric(5,2) DEFAULT 0.0;
ALTER TABLE orders ALTER COLUMN workload SET DEFAULT 0.0;
