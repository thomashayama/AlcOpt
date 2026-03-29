-- schema.sql

# Stores each carboy
# volume in liters
CREATE TABLE IF NOT EXISTS carboy (
    id int AUTOINCREMENT PRIMARY KEY, 
    date_added date NOT NULL,
    retired BOOLEAN NOT NULL DEFAULT false,
    volume FLOAT(2) NOT NULL DEFAULT 2.0
);

CREATE TABLE IF NOT EXISTS bottle (
    id int AUTOINCREMENT PRIMARY KEY,
    date_added date NOT NULL,
    retired BOOLEAN NOT NULL DEFAULT false,
    volume FLOAT(2) NOT NULL DEFAULT 0.75
);

# Brew stores each individual brewing session
CREATE TABLE IF NOT EXISTS brew (
    id int AUTOINCREMENT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS brew_notes (
    note_id int AUTOINCREMENT PRIMARY KEY,
    note_date DATE NOT NULL,
    note TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS carboy_actions (
    action_id int AUTOINCREMENT PRIMARY KEY,
    carboy_id int NOT NULL FOREIGN KEY REFERENCES carboy(carboy_id), 
    brew_id int NOT NULL FOREIGN KEY REFERENCES brew(brew_id), 
    date_added date NOT NULL,
    carboy_state int NOT NULL,
    notes varchar(255)
);

CREATE TABLE IF NOT EXISTS action_ingredients (
    action_id int FOREIGN KEY REFERENCES carboy_actions(action_id),
    carboy_id int NOT NULL FOREIGN KEY REFERENCES carboy(carboy_id), 
    date_added date NOT NULL,
    carboy_state int NOT NULL
);

CREATE TABLE IF NOT EXISTS ingredients (
    ingredient_name TEXT NOT NULL PRIMARY KEY,
    sugar_content float(4) NOT NULL, 
    density float(4),
    notes TEXT
);

CREATE TABLE IF NOT EXISTS tasting (
    brew_id int, 
    username TEXT NOT NULL, 
    taste_date DATE,
    rating float(2), 
    bold float(2), 
    tannic float(2), 
    sweet float(2), 
    acidic float(2), 
    complexity float(2)
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
