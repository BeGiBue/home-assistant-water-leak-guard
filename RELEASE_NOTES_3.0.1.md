# Water Leak Guard 3.0.1

Kleine Korrektur an Beschriftungen, ohne Änderung an Erkennung, Alarmgrenzen oder Quittierung.

- **Karte:** Der grüne Hinweis heißt jetzt **„Hydraulische Überwachung aktiv“** (englisch „Hydraulic monitoring active“).
- **Einheiten:** In deutschen Texten steht Liter als `l` (`l/h`), in englischen als `L` (`L/h`). Das gilt für die Karte, den deutschen Benachrichtigungstext „Aktueller Durchfluss“, die Zahlenfelder im Konfigurationsdialog und die deutschen Wiki-Seiten. Die Einheit der Home-Assistant-Entitäten bleibt `L/h`, weil Home Assistant sie so vorgibt; die Integration liest beide Schreibweisen.
- Die Versionsangaben von Integration, Paket und Karte sind auf 3.0.1 vereinheitlicht.

Für dieses Update ist keine Migration nötig. Nach dem Update Home Assistant neu starten und das Frontend neu laden (bei der Companion-App den Frontend-Cache zurücksetzen), damit die neue Beschriftung erscheint.

Geprüft: Kartentests (50), Validate, Hassfest und HACS-Prüfung. Nicht auf einem echten Gerät getestet.
