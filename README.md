# Lernbrief-Hub

Lernbrief-Hub ist eine lokale Windows-Software (Web-App), um Lerngruppen, Schüler, Kompetenzen und Bewertungen pro Halbjahr zu verwalten und daraus per Knopfdruck Lernbriefe zu erzeugen.

## Funktionen

- Lerngruppen mit Schülerlisten verwalten
- Globale Kompetenzen (für alle Schüler gleiche Vorgaben)
- Bewertung pro Schüler und Kompetenz je Halbjahr (Noten 1 bis 6)
- Mehrere bearbeitbare Satzbausteine je Kompetenz und Note
- Eigene Lernbriefvorlagen mit Tabs: anlegen, speichern, aktiv setzen, löschen
- Header und Footer als Rich-Text pro Vorlage bearbeitbar
- Header- und Footer-Position je Vorlage steuerbar (z. B. Header oben oder nach Einleitung)
- Einheitlicher Textstil pro Vorlage (Schriftart und Schriftgröße)
- Rich-Text-Editor für erzeugte Lernbriefe (fett, kursiv, unterstrichen, Schriftart, Schriftgröße)
- Automatische Lernbrief-Generierung aus Bewertungen mit sinnvoller Absatzstruktur
- Speicherung aller erzeugten Lernbriefe beim jeweiligen Schüler (Historie)
- Export fertiger Lernbriefe als PDF und Word (.docx) mit Rich-Text-Basisformatierungen
- Verbesserte Umbruchlogik für Header/Footer und Export (keine ungewollten Zusatzleerzeilen)
- Übersicht mit Kennzahlen, Halbjahresauswertung und zuletzt gespeicherten Lernbriefen

## Technologie

- Python 3.11+
- Flask
- SQLite (mobile/embedded Datenbank in einer Datei)

## Start unter Windows

1. Terminal im Projektordner öffnen.
2. Virtuelle Umgebung anlegen:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Pakete installieren:

   ```powershell
   pip install -r requirements.txt
   ```

4. Anwendung starten:

   ```powershell
   py app.py
   ```

5. Im Browser öffnen:

   `http://127.0.0.1:5000`

Hinweis: Beim Start wird der Browser automatisch geöffnet, sobald der Server bereit ist.

## Hinweise

- Die Datei `lernbrief_hub.db` wird beim ersten Start automatisch erzeugt.
- Standard-Kompetenzen und Standard-Satzbausteine werden einmalig automatisch angelegt.
- Platzhalter `{name}` kann in Satzbausteinen genutzt werden, um den Schülernamen einzusetzen.
- In Lernbriefvorlagen stehen zusätzlich Platzhalter wie `{group_name}`, `{semester}`, `{avg_grade}` und `{avg_text}` zur Verfügung.
- Bei der Briefgenerierung wird je Kompetenz zufällig ein passender Satz zur jeweiligen Note verwendet.
- Bewertungen und erzeugte Lernbriefe werden pro Halbjahr gespeichert und historisch angezeigt.
- Vorlagenanpassungen gelten für neu erzeugte Lernbriefe.
- Bereits gespeicherte Lernbriefe bleiben unverändert, bis sie neu erzeugt oder manuell bearbeitet werden.

## Betrieb ohne Python auf dem Ziel-PC (Windows)

Wenn auf dem Zielrechner kein Python installiert werden darf, kann die Software als EXE bereitgestellt werden.

1. Build auf einem separaten Rechner durchführen (mit Python-Rechten).
2. Im Projektordner ausführen:

   ```powershell
   .\build_windows.ps1
   ```

   Das Skript installiert automatisch eine mit aktuellen Python-Versionen (z. B. 3.14) kompatible PyInstaller-Version.

3. Ergebnis liegt hier:

   `dist\Lernbrief-Hub.exe`

4. Die Datei `dist\Lernbrief-Hub.exe` auf den Ziel-PC kopieren und dort starten.

Wichtig:

- Auf dem Ziel-PC wird kein Python benötigt.
- Die Datenbank liegt im selben Ordner wie die gestartete EXE:
   `lernbrief_hub.db`
- Auch bei der EXE wird der Browser automatisch geöffnet.

Optionale Umgebungsvariablen:

- `LERNBRIEF_OPEN_BROWSER=0` deaktiviert das automatische Öffnen.
- `LERNBRIEF_HOST` und `LERNBRIEF_PORT` steuern Bind-Adresse und Port.
