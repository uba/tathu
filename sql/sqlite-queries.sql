-- SQLite Example Queries --
-- Author: Douglas Uba <douglas.uba@inpe.br>

-- Load SpatiaLite support
SELECT load_extension('mod_spatialite');

-- Quantos sistemas convectivos ocorreram?
SELECT COUNT(DISTINCT name) FROM systems;

-- Quantos sistemas convectivos ocorreram e duraram mais de x horas?
SELECT COUNT(name)
FROM (SELECT name, (MAX(julianday(date_time)) - MIN(julianday(date_time))) * 24 AS elapsed_time FROM systems GROUP BY(name)) duration
WHERE elapsed_time > x;

-- Quantos sistemas convectivos foram detectados em apenas um instante (i.e. em uma única imagem)?
SELECT COUNT(name)
FROM (SELECT name, (MAX(julianday(date_time)) - MIN(julianday(date_time))) * 24 AS elapsed_time FROM systems GROUP BY(name)) duration
WHERE elapsed_time = 0;

-- Qual o tempo de vida média dos sistemas convectivos?
SELECT AVG(elapsed_time)
FROM (SELECT name, (MAX(julianday(date_time)) - MIN(julianday(date_time))) * 24 AS elapsed_time FROM systems GROUP BY(name)) duration;

-- Qual sistema convectivo durou mais tempo?
SELECT name, (MAX(julianday(date_time)) - MIN(julianday(date_time))) * 24 AS elapsed_time FROM systems
GROUP BY(name) ORDER BY(elapsed_time) DESC LIMIT 1;

-- Quais eventos ocorreram no sistema x?
SELECT event, date_time FROM systems WHERE name='x';

-- Calcula os centroides do sistema convectivo de nome 'x' para cada instante de tempo.
SELECT name, ST_AsText(ST_Centroid(geom)), date_time FROM systems WHERE name = 'x' ORDER BY(date_time);
