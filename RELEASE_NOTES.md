# Release Notes

## Lernbrief-Hub v1.2.5 (30.05.2026)

### Seit v1.2.0 neu
- Fix fuer zusaetzliche Leerzeilen im Export (PDF/Word), wenn Header-Zeilen direkt untereinander stehen.
- HTML-Parser fuer Rich-Text wurde bei Block-Tags (p/div) so angepasst, dass Absatzgrenzen nicht doppelt erzeugt werden.
- Header- und Footer-Inhalte aus Vorlagen werden vor der Lernbrief-Erstellung gezielt normalisiert.
- Block-Wrapper aus dem Rich-Editor (p/div) werden fuer Header/Footer in einfache Zeilenumbrueche ueberfuehrt.
- Mehrfache Zeilenumbrueche in Header/Footer werden zusammengefuehrt; fuehrende und nachgestellte Umbrueche werden entfernt.
- Ergebnis: Wenn im Header-Template kein Zeilenumbruch gesetzt ist, erscheint auch im erzeugten Lernbrief-Textfeld kein ungewollter Zusatzumbruch.

### Kompatibilitaet
- Keine manuelle Migration erforderlich.
- Die Anpassungen wirken auf neu erzeugte Lernbriefe; bereits gespeicherte Inhalte bleiben unveraendert, bis sie neu erzeugt oder bearbeitet werden.

## Lernbrief-Hub v1.2.0 (30.05.2026)

### Seit v1.1.0 neu
- Eigene Seite Lernbriefvorlagen als separater Navigationspunkt hinzugefuegt.
- Mehrere Lernbriefvorlagen mit Tabs: anlegen, umbenennen, speichern, aktiv setzen und loeschen.
- Vorlagenaenderungen greifen nun direkt bei neu erzeugten Lernbriefen (aktive Vorlage wird verwendet).

### Lernbriefvorlagen und Layout
- Header und Footer sind als Rich-Text in den Vorlagen bearbeitbar.
- Positionierung pro Vorlage: Header oben oder nach Einleitung, Footer am Ende oder direkt nach dem Header.
- Einheitlicher Textstil pro Vorlage fuer den Briefinhalt (Schriftart und Schriftgroesse).
- Schriftgroesse kann jetzt bis auf 4 heruntergesetzt werden (vorher Mindestwert 11).
- Optionaler Notendurchschnitts-Satz bleibt je Vorlage ein- und ausschaltbar sowie frei bearbeitbar.

### Bedienung fuer Nicht-IT-Nutzer
- Kurze Platzhalter-Erklaerungen direkt an den relevanten Bearbeitungsstellen ergaenzt.
- Platzhalterhilfe beschreibt knapp, welche Daten z. B. bei {name}, {group_name}, {semester}, {avg_grade} eingesetzt werden.

### Lernbrief-Editor und Generierung
- Lernbrief-Ansicht verwendet einen Rich-Text-Editor mit Werkzeugen (u. a. fett, kursiv, unterstrichen, Schriftart, Schriftgroesse).
- Generierte Lernbriefe werden als Berichtstext aufgebaut (keine reine Stichpunktliste), inkl. sinnvoller Absatzstruktur.
- Satzbaustein-Seite fokussiert wieder auf Satzbausteine; Vorlagenverwaltung wurde ausgelagert.

### Export (PDF/Word)
- PDF- und Word-Export uebernehmen nun Rich-Text-Formatierungen aus dem Lernbrief deutlich besser.
- Absatze, Zeilenumbrueche und Basisformatierungen (fett/kursiv/unterstrichen) werden im Export beruecksichtigt.
- Export verwendet den zur Vorlage gehoerenden Schriftsnapshot des gespeicherten Lernbriefs.

### Deployment und Betrieb
- Build auf One-File-EXE umgestellt; Problem mit fehlender python DLL aus _internal beim Verschieben beseitigt.
- Datenbank wird im EXE-Betrieb im gleichen Ordner wie die EXE verwendet.
- Build-Skript auf aktuelle PyInstaller-Kompatibilitaet (u. a. Python 3.14) angepasst.
- Stopskript fuer Lernbrief-Hub-Prozesse bereitgestellt.

## Lernbrief-Hub v1.1.0 (30.05.2026)

### Seit v1.0.0 neu
- Neue Gesamtuebersicht mit zentralen Kennzahlen (Schueler, Lerngruppen, Bewertungen, Lernbriefe, Kompetenzen).
- Neue Halbjahres- und Aktivitaetsauswertung inklusive aktueller Werte und Verlauf.
- Neue Ansicht der groessten Lerngruppen mit Direktzugriff.
- Neue Anzeige der zuletzt gespeicherten Lernbriefe in der Uebersicht.
- Navigationspunkt Uebersicht in der Kopfleiste integriert.

### Lernbrief-Editor und Vorlagen
- Lernbrief-Header ist jetzt personalisierbar.
- Header-Template mit Platzhaltern wie {name}, {group_name}, {semester}, {avg_grade}, {avg_text}.
- Footer/Abschlusssatz bleibt konfigurierbar und wurde funktional mit dem Header-Bereich zusammengefuehrt.
- Der Bearbeitungsbereich fuer Header/Footer wurde visuell ueberarbeitet (klare Kartenstruktur, bessere Lesbarkeit, responsive Layout).

### Bewertungen
- Feld Zusatz / Beobachtung wurde auf ein echtes, mehrzeiliges Textfeld umgestellt.
- Das Beobachtungsfeld ist vertikal aufziehbar (Resize) fuer laengere Eintraege.

### Export
- Der technische Zusatzkopf im Export wurde entfernt.
- PDF- und Word-Exporte enthalten nun nur noch den eigentlichen Lernbriefinhalt.

### Kompatibilitaet
- Keine Migration durch den Benutzer erforderlich.
- Bestehende Daten in lernbrief_hub.db bleiben unveraendert nutzbar.

## Lernbrief-Hub v1.0.0 (30.05.2026)

### Highlights
- Zentrale Verwaltung von Lerngruppen, Schuelerinnen und Schuelern sowie Kompetenzprofilen in einer lokalen Anwendung.
- Erstellung von Lernbriefen per Knopfdruck auf Basis der erfassten Bewertungen.
- Export von Lernbriefen als PDF und Word-Datei (.docx).

### Neu in dieser Version
- Lerngruppenverwaltung mit Uebersicht und direktem Zugriff auf Schuelerlisten.
- Schuelersuche nach Name oder Lerngruppe auf der Startseite.
- Kompetenzverwaltung inklusive Bearbeitung von Name, Beschreibung und Sortierreihenfolge.
- Bewertungsmaske pro Schueler, Kompetenz und Halbjahr (Noten 1 bis 6) mit optionalen Hinweisen.
- Halbjahreslogik mit standardisiertem Schuljahresformat (YYYY/YYYY-HJ1 oder HJ2).
- Bearbeitbare Satzbausteine pro Kompetenz und Note mit Mehrfachvarianten.
- Platzhalterunterstuetzung mit {name} in Satzbausteinen.
- Konfigurierbarer Abschlusssatz zur Durchschnittsnote in Lernbriefen.
- Historie pro Schueler: Bewertungen, Semesteruebersicht und erzeugte Lernbriefe.
- Anzeige kuerzlich erzeugter Lernbriefe im Dashboard.
- Loeschen einzelner Lernbriefe direkt aus der Anwendung.

### Generierung und Ausgabe
- Automatische Lernbrief-Generierung aus den aktuellen Bewertungen eines Halbjahres.
- Zufallsauswahl passender Satzbausteine je Kompetenz und Note fuer abwechslungsreiche Formulierungen.
- Automatische Formatnormalisierung fuer mehrzeilige Satzbausteine und Satzzeichen.
- Export mit sprechenden Dateinamen im Format Lernbrief_<Name>_<Halbjahr>.

### Technische Basis
- Python 3.11+, Flask und SQLite als lokale Datenbasis.
- Automatische Initialisierung der Datenbank beim ersten Start.
- Automatisches Anlegen von Standard-Kompetenzen und Standard-Satzbausteinen.
- Betrieb als lokale Web-App mit optionalem Browser-Autostart.
- Bereitstellung als eigenstaendige Windows-EXE via Build-Skript.

### Konfiguration
- LERNBRIEF_OPEN_BROWSER=0 deaktiviert den Browser-Autostart.
- LERNBRIEF_HOST und LERNBRIEF_PORT steuern Adresse und Port der Anwendung.

### Hinweise
- Die Anwendung speichert alle Daten lokal in der Datei lernbrief_hub.db.
- Zielgruppe dieser Version ist der produktive lokale Einsatz in Schule und Lernbegleitung ohne Cloud-Abhaengigkeit.
