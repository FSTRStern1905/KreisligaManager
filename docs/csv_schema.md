# KreisligaManager – CSV-Importschema

Dieses Dokument beschreibt den verbindlichen Aufbau aller CSV-Importdateien.

## Allgemeine Regeln

- Dateiformat: CSV
- Zeichencodierung: UTF-8
- Trennzeichen: Komma
- Erste Zeile: Spaltenüberschriften
- Datumsformat: `YYYY-MM-DD`
- Zeitformat: `HH:MM`
- Leere optionale Werte bleiben leer
- IDs müssen eindeutig sein

---

# clubs.csv

## Spalten

| Spalte | Typ | Pflicht | Beschreibung |
|---|---|:---:|---|
| club_id | TEXT | ✅ | Eindeutige Vereins-ID, zum Beispiel `c_0001` |
| club_name | TEXT | ✅ | Vollständiger Vereinsname |
| club_short_name | TEXT | ✅ | Kurzname des Vereins |
| association | TEXT | ✅ | Zuständiger Verband, zum Beispiel `FVR` |
| country | TEXT | ✅ | Land |
| founded | INTEGER | ❌ | Gründungsjahr |
| city | TEXT | ❌ | Ort des Vereins |
| website | TEXT | ❌ | Internetseite |
| logo | TEXT | ❌ | Dateipfad oder Dateiname des Vereinslogos |

## Kopfzeile

```csv
club_id,club_name,club_short_name,association,country,founded,city,website,logo

# events.csv

## Spalten

| Spalte | Typ | Pflicht | Beschreibung |
|---|---|:---:|---|
| event_id | TEXT | ✅ | Eindeutige Ereignis-ID |
| match_id | TEXT | ✅ | Zugehörige Spiel-ID |
| minute | INTEGER | ✅ | Spielminute |
| event_type | TEXT | ✅ | Typ des Ereignisses |
| team_id | TEXT | ✅ | Zugehörige Mannschafts-ID |
| player_id | TEXT | ❌ | Hauptspieler des Ereignisses |
| related_player_id | TEXT | ❌ | Zweiter beteiligter Spieler |
| value | TEXT | ❌ | Zusätzlicher Wert |
| comment | TEXT | ❌ | Freitextkommentar |

## Kopfzeile

```csv
event_id,match_id,minute,event_type,team_id,player_id,related_player_id,value,comment
```

## Vorgesehene Ereignistypen

| Wert | Bedeutung |
|---|---|
| goal | Tor |
| own_goal | Eigentor |
| penalty_goal | Verwandelter Elfmeter |
| penalty_missed | Verschossener Elfmeter |
| yellow_card | Gelbe Karte |
| second_yellow_card | Gelb-Rote Karte |
| red_card | Rote Karte |
| substitution | Spielerwechsel |
| injury | Verletzung |
| assist | Torvorlage |