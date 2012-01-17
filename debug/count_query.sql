SELECT games.name, games.id, COUNT(servers.app_id) 
FROM games 
INNER JOIN servers 
ON games.id = servers.app_id 
GROUP BY games.name, games.id 
ORDER BY COUNT(servers.app_id) DESC;

