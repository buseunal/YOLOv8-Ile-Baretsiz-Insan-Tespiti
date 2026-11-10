-- 1) Bugün kamera başına ihlal sayısı (n8n akşam raporu bunu kullanır)
SELECT camera_id, COUNT(*) AS ihlal_sayisi
FROM violations
WHERE detected_at >= CURRENT_DATE
GROUP BY camera_id
ORDER BY ihlal_sayisi DESC;

-- 2) Saat saat ihlal dağılımı (hangi saatlerde sorun çıkıyor?)
SELECT DATE_TRUNC('hour', detected_at) AS saat, COUNT(*) AS ihlal_sayisi
FROM violations
WHERE detected_at >= CURRENT_DATE
GROUP BY saat
ORDER BY saat;

-- 3) Son 10 ihlal
SELECT id, camera_id, violation_type, confidence, detected_at
FROM violations
ORDER BY detected_at DESC
LIMIT 10;

-- 4) Kamera başına ortalama güven skoru
SELECT camera_id, ROUND(AVG(confidence), 3) AS ort_guven, COUNT(*) AS adet
FROM violations
GROUP BY camera_id
HAVING COUNT(*) >= 2
ORDER BY ort_guven DESC;
