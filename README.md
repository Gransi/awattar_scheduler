# awattar_scheduler
Dieser Python Skript analysiert die stündlichen Strompreise der Strombörse von aWATTar Hourly (https://www.awattar.com/tariffs/hourly) und sucht den günstigsten Zeitpunkt zum Einschalten von elektrischen Verbrauchern.

Beim Ausführen des Skriptes werden die Start- und Endzeit Marker in der Template Datei entsprechend der Einstellungen gesetzt. Das Ergebnis wird in das Output Verzeichnis kopiert. 

Somit kann man zum Beispiel Cron Jobs erstellen, welche elektrische Verbraucher, zum Beispiel Heizungen, Pumpen, Warmwasseraufbereitung, Geschirrspüler usw. zu einem günstigen Strompreis ein und ausschalten.

Bei Bedarf werden die Strombörsendaten in eine InfluxDB Databank gespeichert.

# Mögliche Verwendungszwecke
-Cron Jobs erstellen
-InfluxDB Daten mit Grafana auswerten
-OpenHab Rule Dateien erstellen
-usw



# Installation

1. Kopiere den Inhalte von etc auf das lokalen etc Verzeichnis
2. Kopiere awattar_scheduler.py in das /usr/local/bin Verzeichnis
3. Die Parameter in der awattar_scheduler.conf anpassen

# Task Einstellungen
Alle Task Sektion Name müssen mit "Task_" beginnen

**Enable:**
	Aktivieren oder Deaktivieren [true|false]

**Starttime:**
	Startzeitpunkt der Analyse

**Periode:**
	Wie viele Stunden sollen ab den Startzeitpunkt berücksichtigt werden. 

**Duration:**
	Wie viele Stunden wird für die Last benötigt.

**Template:**
	Pfad zur Template Datei

**Output:**
	Das Ergebnis wird in die Datei abgelegt.

**Starttimepattern:**
	Formartiert den Startzeitpunkt in das entsprechende Format. z.B. Time cron "0 %%M %%H * * ?" -> Time cron "0 0 13 * * ?"

**Endtimepattern:**
	Formartiert den Endzeitpunkt in das entsprechende Format. z.B. Time cron "0 %%M %%H * * ?" -> Time cron "0 0 13 * * ?"
