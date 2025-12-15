CREATE DATABASE IF NOT EXISTS viedb;
USE viedb;

CREATE TABLE IF NOT EXISTS Vie (
    lid BIGINT PRIMARY KEY AUTO_INCREMENT,
    libelle VARCHAR(100) NOT NULL,
    nombreVieInitiale INT
);

-- Données initiales pour les pièces d'échecs
-- R = Tour (Rook), N = Cavalier (Knight), B = Fou (Bishop)
-- Q = Reine (Queen), K = Roi (King)
INSERT INTO Vie (libelle, nombreVieInitiale) VALUES
('Tour (R)', 5),
('Cavalier (N)', 4),
('Fou (B)', 5),
('Reine (Q)', 8),
('Roi (K)', 10),
('Pion (P)', 2);