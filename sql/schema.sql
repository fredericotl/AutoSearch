   -- Schema for AutoSearch (PostgreSQL)
   -- Usage: createdb autosearch && psql -d autosearch -f sql/schema.sql

CREATE TABLE users (
	id SERIAL,
	email TEXT NOT NULL UNIQUE,
	username TEXT NOT NULL UNIQUE,
	first_name TEXT NOT NULL,
	last_name TEXT,
	hashed_password TEXT NOT NULL,
	is_active BOOLEAN,
	role TEXT,
	PRIMARY KEY(id)
);

CREATE TABLE products (
	id SERIAL,
	title TEXT NOT NULL,
	link TEXT NOT NULL,
	specification TEXT,
	owner_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
	is_search_active BOOLEAN,
	PRIMARY KEY(id)
);

CREATE TABLE product_viewers(
	product_id	INTEGER	NOT NULL REFERENCES products(id) ON DELETE CASCADE,
	user_id	INTEGER	NOT NULL REFERENCES users(id) ON DELETE CASCADE,
	PRIMARY KEY (product_id, user_id)
);

CREATE TABLE price_history (
	id SERIAL,
	product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
	price INTEGER,
	captured_at TIMESTAMP NOT NULL,
	PRIMARY KEY(id)
);

CREATE INDEX ix_product_captured ON price_history (product_id, captured_at);


CREATE TABLE detections (
	id SERIAL,
	product_id INTEGER REFERENCES products(id) ON DELETE SET NULL,
	user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
	criteria TEXT NOT NULL,
	price INTEGER NOT NULL,
	detected_at TIMESTAMP NOT NULL,
	sent_at TIMESTAMP,
	PRIMARY KEY(id)
);

CREATE INDEX ix_detections_sent_at ON detections (sent_at);

CREATE TABLE errors (
	id SERIAL,
	source TEXT NOT NULL,
	product_id INTEGER REFERENCES products(id) ON DELETE SET NULL,
	user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
	error_type TEXT NOT NULL,
	message TEXT ,
	captured_at TIMESTAMP NOT NULL,
	is_fixed BOOLEAN NOT NULL,
	PRIMARY KEY(id)
);

CREATE INDEX ix_errors_source_captured ON errors (source, captured_at);

CREATE INDEX ix_errors_product_captured ON errors (product_id, captured_at);

