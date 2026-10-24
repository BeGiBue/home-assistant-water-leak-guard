# Water Leak Guard 3.0.0 (geplant)

Water Leak Guard wurde in den offiziellen HACS-Katalog aufgenommen. Neue Installationen verwenden die HACS-Suche nach **Water Leak Guard**.

Bestehende Custom-Repository-Installationen: zuerst die Verfügbarkeit im offiziellen Katalog prüfen, dann nur den Eintrag unter **Benutzerdefinierte Repositories** entfernen. Die Installation nicht deinstallieren. HACS aktualisieren und Installation sowie Updates prüfen. Konfigurationseinträge, Entitäten, Automationen und Dashboard-Karten bleiben erhalten; nach Updates Home Assistant neu starten und Frontend neu laden.

Die Major-Version markiert die HACS-Aufnahme und bedeutet nicht automatisch Breaking Changes. Für dieses Update ist keine Konfigurationsmigration erforderlich. Die Versionsangaben der Integration und der mitgelieferten Karte werden auf 3.0.0 vereinheitlicht.

Der Security-Review korrigiert eine blockierende Dateisystemabfrage beim Start. Backend-Autorisierung, Quittierung, Alarmgrenzen und Ventilsteuerung werden dadurch nicht verändert. Regressionstest und bestehende Prüfungen sind in [SECURITY_REVIEW.md](SECURITY_REVIEW.md) dokumentiert.

Diese Datei bereitet das Release vor; es wurde kein Tag oder GitHub-Release angelegt. Vor Veröffentlichung sind die vollständige Validierung und die bestehenden manuellen Home-Assistant-/Companion-/Hardware-Prüfungen erforderlich.
