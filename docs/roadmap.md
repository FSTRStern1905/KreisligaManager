# KreisligaManager – Roadmap

## Projektziel

Der KreisligaManager soll eine Desktop-Anwendung für den Amateurfußball werden.

Die Anwendung soll echte und simulierte Fußball-Daten verwalten, auswerten und darstellen können.

Langfristig sollen unter anderem folgende Bereiche abgedeckt werden:

- Vereine
- Mannschaften
- Spieler
- Saisons
- Ligen
- Spielpläne
- Ergebnisse
- Tabellen
- Ereignisse
- Statistiken
- Importe
- Exporte
- Saison-Simulationen

---

# Version 0.2 – Grundsystem

## Status: In Entwicklung

### Fertig

- [x] Python-Projektstruktur
- [x] Virtuelle Python-Umgebung
- [x] Git und GitHub
- [x] SQLite-Datenbank
- [x] Automatische Tabellenerstellung
- [x] PySide6-GUI
- [x] Dark Theme
- [x] Hauptfenster
- [x] Sidebar
- [x] Dashboard
- [x] Vereinsseite
- [x] Vereine suchen
- [x] Vereine dauerhaft speichern
- [x] Saisonseite
- [x] Saisons dauerhaft speichern
- [x] Mannschaftsseite
- [x] Mannschaften Vereinen zuordnen
- [x] Mannschaften dauerhaft speichern
- [x] Demo-Generator
- [x] 12 Demo-Vereine
- [x] 264 Demo-Spieler
- [x] Spielplangenerator
- [x] Hin- und Rückrunde
- [x] 22 Spieltage bei 12 Mannschaften
- [x] 132 Spiele bei 12 Mannschaften
- [x] Spiele dauerhaft in SQLite speichern
- [x] Spiele nach Spieltagen anzeigen
- [x] Spiele suchen
- [x] Seiten beim Öffnen automatisch aktualisieren
- [x] Doppeltes Erzeugen eines Spielplans verhindern

### Offen

- [ ] Vereine bearbeiten
- [ ] Vereine löschen
- [ ] Saisons bearbeiten
- [ ] Saisons löschen
- [ ] Mannschaften bearbeiten
- [ ] Mannschaften löschen
- [ ] Mannschaften gezielt einer Saison oder Liga zuweisen
- [ ] Spielplan nur aus ausgewählten Mannschaften erzeugen
- [ ] Spielplan löschen oder neu erzeugen
- [ ] Datum und Uhrzeit für Spiele erzeugen
- [ ] Liga-Auswahl beim Spielplan
- [ ] Bessere Darstellung der Spiele-Seite

---

# Version 0.3 – Stammdaten

## Spieler

- [ ] Spielerseite
- [ ] Spieler suchen
- [ ] Spieler anlegen
- [ ] Spieler bearbeiten
- [ ] Spieler löschen
- [ ] Spieler einer Mannschaft zuweisen
- [ ] Vorname
- [ ] Nachname
- [ ] Geburtsdatum
- [ ] Position
- [ ] Trikotnummer
- [ ] Starker Fuß
- [ ] Aktiv oder inaktiv

## Weitere Stammdaten

- [ ] Länder
- [ ] Verbände
- [ ] Ligen
- [ ] Stadien
- [ ] Schiedsrichter
- [ ] Trainer
- [ ] Betreuer

---

# Version 0.4 – Saison und Wettbewerb

- [ ] Saison einer Liga zuordnen
- [ ] Mannschaften einer Liga und Saison zuordnen
- [ ] Anzahl der Mannschaften frei auswählen
- [ ] Spielplan validieren
- [ ] Heim- und Auswärtsverteilung prüfen
- [ ] Freilose bei ungerader Mannschaftszahl
- [ ] Spieltage verschieben
- [ ] Spiele verlegen
- [ ] Spielstatus verwalten

Mögliche Spielstatus:

- Geplant
- Live
- Beendet
- Verlegt
- Abgebrochen
- Abgesagt

---

# Version 0.5 – Spielverwaltung

- [ ] Ergebnis erfassen
- [ ] Halbzeitstand erfassen
- [ ] Aufstellung erfassen
- [ ] Startelf
- [ ] Ersatzbank
- [ ] Formation
- [ ] Einwechslungen
- [ ] Auswechslungen
- [ ] Tore
- [ ] Eigentore
- [ ] Gelbe Karten
- [ ] Gelb-Rote Karten
- [ ] Rote Karten
- [ ] Elfmeter
- [ ] Verletzungen
- [ ] Zuschauer
- [ ] Wetter
- [ ] Schiedsrichter

---

# Version 0.6 – Tabellen und Statistiken

## Tabelle

- [ ] Spiele
- [ ] Siege
- [ ] Unentschieden
- [ ] Niederlagen
- [ ] Tore
- [ ] Gegentore
- [ ] Tordifferenz
- [ ] Punkte

## Mannschaftsstatistiken

- [ ] Durchschnittliche Tore
- [ ] Durchschnittliche Gegentore
- [ ] Heimtabelle
- [ ] Auswärtstabelle
- [ ] Form der letzten 5 Spiele
- [ ] Form der letzten 10 Spiele
- [ ] Punkteverlauf
- [ ] Siegesserien
- [ ] Niederlagenserien
- [ ] Spiele ohne Gegentor
- [ ] Höchster Sieg
- [ ] Höchste Niederlage
- [ ] Tore nach Spielminuten
- [ ] Gegentore nach Spielminuten

## Spielerstatistiken

- [ ] Einsätze
- [ ] Startelfeinsätze
- [ ] Einwechslungen
- [ ] Auswechslungen
- [ ] Spielminuten
- [ ] Tore
- [ ] Vorlagen
- [ ] Karten
- [ ] Joker-Tore
- [ ] Elfmeter
- [ ] Torbeteiligungen

---

# Version 0.7 – Import und Export

## Import

- [ ] CSV
- [ ] Excel
- [ ] fussball.de
- [ ] FuPa
- [ ] Screenshots
- [ ] OCR

## Export

- [ ] CSV
- [ ] Excel
- [ ] PDF
- [ ] Tabellen
- [ ] Spielerstatistiken
- [ ] Spielberichte
- [ ] Saisonberichte

---

# Version 0.8 – Simulation

- [ ] Mannschaftsstärken
- [ ] Spielerstärken
- [ ] Form
- [ ] Moral
- [ ] Fitness
- [ ] Heimvorteil
- [ ] Verletzungen
- [ ] Sperren
- [ ] Zufalls-Engine
- [ ] Reproduzierbare Simulationen mit Seed
- [ ] Einzelspiel simulieren
- [ ] Spieltag simulieren
- [ ] Saison simulieren
- [ ] Mehrfachsimulationen

Beispiele:

- 100 Simulationen
- 1.000 Simulationen
- 10.000 Simulationen

Mögliche Auswertungen:

- Meisterwahrscheinlichkeit
- Aufstiegswahrscheinlichkeit
- Top-3-Wahrscheinlichkeit
- Abstiegswahrscheinlichkeit
- Erwartete Punkte
- Erwartete Platzierung

---

# Version 1.0 – Erstes vollständiges Release

- [ ] Stabile Windows-Anwendung
- [ ] EXE-Datei
- [ ] Automatische Datenbank-Backups
- [ ] Fehlerprotokoll
- [ ] Einstellungen
- [ ] Benutzerfreundliche Dialoge
- [ ] Vollständige Dokumentation
- [ ] Import echter Saisons
- [ ] Spielpläne
- [ ] Tabellen
- [ ] Statistiken
- [ ] Grundlegende Simulation
- [ ] Excel- und PDF-Export

---

# Aktueller nächster Sprint

## Projektbereinigung

- [ ] Alte und doppelte Dateien prüfen
- [ ] Nicht verwendete Dateien entfernen
- [ ] Imports kontrollieren
- [ ] Testdateien prüfen
- [ ] Projektstruktur dokumentieren
- [ ] Git-Status prüfen
- [ ] Commit und Push

## Danach

- [ ] Spielerverwaltung beginnen