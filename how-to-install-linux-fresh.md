# Installation Flask und Dergleichen

Auf einer frischen Ubuntu Installation haben wir zwar schon einige Tools dabei, aber nur um sicher zu gehen, installieren wir hier trotzdem alle, die wir brauchen:
	- git
	- python
	- pip
	- flask
	- pymongo
Natürlich brauchen wir auch unser Github-Repo aber das holen wir uns dann einfach mit git.
Um die Tools zu installieren, führen wir folgendes aus:
`sudo apt update && sudo apt upgrade` 
`sudo apt-get install git python`
Das installiert uns git und python.
Wenn das alles geklappt hat, führen wir nun `sudo apt-get install pip` aus, damit installieren wir den python package manager. Theoretisch könnte man den auch in einem Rutsch mit git und python installieren, aber ich glaube dass pip als abhängigkeit python hat, also ist es wahrscheinlich besser, zuerst python zu installieren.
Ist pip fertig installiert, können wir mit `pip install flask` flask und mit `pip install pymongo` pymongo installieren.
Das sollte funktionieren, allerdings bekommen wir (ggf.) eine Warnung.
Flask wurde installiert aber nicht unserer PATH-variablen hinzugefügt. Die PATH-variable ist eine Systemvariable, in der Dateipfade gespeichert sind. Wenn du dich frägst, wo dein Betriebssystem nach den Binärdateien sucht, wenn du z.b. `git --version` ausführst, dann hast du hier die Antwort gefunden: Das System sucht an allen Orten, die in PATH stehen.
Um also flask stressfrei zu finden, bietet es sich an, dieses zum PATH hinzuzufügen. Das geht auf mehrere Arten:
Mit `export PATH=$PATH:~/.local/bin` wird der Ordner "~/.local/bin" zum PATH hinzugefügt. **DAS IST LEIDER NUR TEMPORÄR**. Um den PATH __persistent__ zu verändern, müssen wir das in einer Datei speichern, und zwar so, dass diese regelmäßig neu geladen wird. Hört sich schlimm an? Nicht wirklich. Diese Datei existiert zum Glück schon und heißt ".bashrc". Die .bashrc liegt in deinem Home-Verzeichnis "~/". Der absolute Pfad zur .bashrc ist also "~/.bashrc". Die .bashrc wird bei jedem start einer Command-Line (bash) neu gelesen. Dort speichern wir nun das `export`-Kommando rein.
Long Story short: Öffne deine .bashrc mit einem Editor deiner Wahl. Das kann so aussehen `vim ~/.bashrc`. Am Ende(!) der Datei fügen wir nun die magische Zeile code ein: `PATH=$PATH:~/.local/bin` Speichere die Datei (mit Vim: `<esc> :w`) und schließe diese (mit Vim `:q`).
Fertig.
Wenn du dein Consolenfenster schließt und wieder öffnet, wird die Datei neu geladen. Alternativ kannst du auch `source ~/.bashrc` eintippen, dann wird die Datei neu geladen.
Wenn alles gut läuft, sollte sich flask jetzt problemlos starten lassen.
Um das zu testen, machen wir einen neuen Ordner: `mkdir sse && cd sse`, dort führen wir `git clone https://github.com/ZecurePOS/ZecurePOS.github.io.git` aus. Wir navigieren nach "ZecurePOS.github.io" (using `cd`) und führen dort `python init.py` aus. Nun gibt es drei mögliche Ausgänge:
	1. Alles funktioniert perfekt -> du bist fertig :)
	2. Error: no module named flask -> siehe Section noModuleNamed
	3. Error: no module named pymongo -> siehe Section noModuleNamed
Erstmal Glückwunsch falls es geklappt hat und viel Spaß.
## noModuleNamed
Falls es nicht geklappt hat, liegt das daran, dass entweder Flask und Pymongo nicht richtig installiert wurden (unwahrscheinlich aber möglich) *oder* was viel wahrscheinlicher ist: deine python-version nicht ganz passt.
Um die Python-Version zu checken gibst du mal `python --version` ein. Ist die Nummer kleiner als 3? Das ist der Fehler. Als quick fix kannst du mal versuchen, `python3 init.py` auszuführen, das sucht dann nach python3. Python3 solltest du mit `apt install python` auch installiert haben. Wenn es funktioniert, ist am schnellsten einfach ab sofort python3 immer zu verwenden, du kannst aber auch schauen wie du hinbekommst, dass standardmäßig python3 ausgeführt wird, wenn du nur `python` eingibst.
Wenn Pymongo nicht gefunden wird, solltest du einfach schauen, ob du das wirklich mit `pip install pymongo` installiert hast, das sollte dann nämlich funktionieren.
Profit.

