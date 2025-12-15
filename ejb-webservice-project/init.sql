CREATE DATABASE IF NOT EXISTS viedb;
USE viedb;

CREATE TABLE IF NOT EXISTS Vie (
    lid BIGINT PRIMARY KEY AUTO_INCREMENT,
    libelle VARCHAR(100) NOT NULL,
    nombreVieInitiale INT
);

-- Données de test
INSERT INTO Vie (libelle, nombreVieInitiale) VALUES
('Vie Standard', 3),
('Vie Bonus', 5),
('Vie Extra', 10);