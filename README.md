# PANTILT_ROS2_Jazzy

ROS-2-Jazzy-Workspace zur Ansteuerung einer Pan-Tilt-Unit (PTU) mit Zielausrichtung und Trigger-Auslösung. Das Repository enthält das Python-Package `aim_and_fire`, ein Docker-Setup sowie Launch-Konfigurationen für den Betrieb mit einer seriellen PTU und einem Mikrocontroller-Trigger.

## Funktionsumfang

- Berechnung von Pan- und Tilt-Sollwinkeln aus einem Zielpunkt auf `/target_point`
- Ausgabe der PTU-Sollpositionen als `sensor_msgs/JointState` auf `/ptu/cmd`
- Überwachung der aktuellen PTU-Position über `/ptu/state`
- Automatisches Auslösen eines Triggers auf `/trigger`, sobald die Zielposition innerhalb einer einstellbaren Toleranz erreicht ist
- Berücksichtigung von Achsversatz, physischem Düsenversatz und ballistischer Kompensation des Wasserstrahls
- Serieller Trigger-Ausgang für einen externen Mikrocontroller
- Service zum Auslösen einer PTU-Referenzfahrt über `/ptu/reference`
- Docker- und Docker-Compose-Unterstützung für ROS 2 Jazzy

## Repository-Struktur

```text
.
├── Dockerfile
├── docker-compose.yml
├── README.md
└── src/
    └── aim_and_fire/
        ├── aim_and_fire/
        │   ├── aim_and_fire_node.py
        │   ├── ptu_reference_node.py
        │   └── trigger_node.py
        ├── launch/
        │   └── aim_and_fire.launch.py
        ├── package.xml
        ├── setup.cfg
        └── setup.py
```

## Systemübersicht

Das System verarbeitet Zielpunkte im PTU-Koordinatensystem und steuert daraus die PTU an. Sobald die Rückmeldung der PTU zeigt, dass Pan- und Tilt-Achse innerhalb der Toleranz liegen, wird ein Trigger-Signal erzeugt.

```text
/target_point
    │ geometry_msgs/Point
    ▼
aim_and_fire_node
    ├── /ptu/cmd       sensor_msgs/JointState
    ├── /ptu/state     sensor_msgs/JointState
    └── /trigger       std_msgs/Bool
                          │
                          ▼
                    trigger_node
                          │ seriell, z. B. /dev/ttyACM0
                          ▼
                    Mikrocontroller
```

Zusätzlich stellt `ptu_reference_node` einen ROS-Service bereit:

```text
/ptu/reference   std_srvs/srv/Trigger
```

## Voraussetzungen

### Software

- ROS 2 Jazzy
- Python 3
- `colcon`
- `python3-serial`
- Docker und Docker Compose, falls der Container-Betrieb genutzt wird

### Hardware

- Pan-Tilt-Unit mit seriellem Anschluss, typischerweise `/dev/ttyUSB0`
- Mikrocontroller für die Trigger-Ausgabe, typischerweise `/dev/ttyACM0`
- Zielpunktquelle, die `geometry_msgs/Point` auf `/target_point` publiziert
- PTU-Treiber, der `/ptu/cmd` annimmt und `/ptu/state` publiziert

Im Dockerfile wird der ROS-2-PTU-Treiber `flir_ptu_driver` automatisch in den Workspace geklont und mitgebaut.

## Installation ohne Docker

Workspace vorbereiten:

```bash
git clone <REPOSITORY_URL>
cd PANTILT_ROS2_Jazzy
```

Externe PTU-Treiberabhängigkeit in den Workspace klonen:

```bash
git clone https://github.com/vicoslab/flir_ptu_driver.git src/flir_ptu_driver
```

Abhängigkeiten installieren:

```bash
sudo apt update
sudo apt install -y python3-colcon-common-extensions python3-serial
rosdep update
rosdep install --from-paths src --ignore-src -r -y
```

Workspace bauen:

```bash
source /opt/ros/jazzy/setup.bash
colcon build
source install/setup.bash
```

System starten:

```bash
ros2 launch aim_and_fire aim_and_fire.launch.py
```

## Betrieb mit Docker Compose

Container bauen und starten:

```bash
docker compose up --build
```

Interaktive Shell im Container öffnen:

```bash
docker compose run --rm pantilt bash
```

Innerhalb des Containers kann der Workspace manuell gebaut und gestartet werden:

```bash
source /opt/ros/jazzy/setup.bash
source /ros2_ws/install/setup.bash
ros2 launch aim_and_fire aim_and_fire.launch.py
```

> Hinweis: In `docker-compose.yml` wird bereits `aim_and_fire.launch.py` gestartet. Der `CMD` im Dockerfile verweist aktuell auf `system.launch.py`; diese Launch-Datei ist im Repository nicht vorhanden. Für einen direkten `docker run` sollte der `CMD` daher auf `aim_and_fire.launch.py` angepasst werden.

## Nodes

### `aim_and_fire`

Berechnet aus einem Zielpunkt die PTU-Sollwinkel und publiziert diese an den PTU-Treiber. Die Node berücksichtigt:

- PTU-Montageoffsets `offset_x`, `offset_y`, `offset_z`
- mechanischen Tilt-Offset `tilt_offset_deg`
- Düsenversatz `tool_offset_z`
- Wasserstrahlgeschwindigkeit `water_speed_m_s`
- Gravitationsbedingte Fallkompensation des Wasserstrahls

Start über Launch-Datei:

```bash
ros2 launch aim_and_fire aim_and_fire.launch.py
```

Direktstart:

```bash
ros2 run aim_and_fire aim_and_fire
```

### `trigger_node`

Abonniert `/trigger` und sendet bei `true` ein Byte `1` über die serielle Schnittstelle an einen Mikrocontroller.

Direktstart:

```bash
ros2 run aim_and_fire trigger_node --ros-args -p port:=/dev/ttyACM0 -p baud_rate:=9600
```

### `ptu_reference_node`

Stellt den Service `/ptu/reference` bereit und sendet bei Aufruf den Referenzfahrtbefehl `R\r` an die PTU.

Direktstart:

```bash
ros2 run aim_and_fire ptu_reference --ros-args -p port:=/dev/ttyUSB0
```

Referenzfahrt auslösen:

```bash
ros2 service call /ptu/reference std_srvs/srv/Trigger {}
```

## Topics und Services

| Name | Typ | Richtung | Beschreibung |
|---|---|---:|---|
| `/target_point` | `geometry_msgs/msg/Point` | Eingang | Zielpunkt relativ zum definierten Koordinatensystem |
| `/ptu/cmd` | `sensor_msgs/msg/JointState` | Ausgang | Sollposition und Geschwindigkeit für Pan- und Tilt-Achse |
| `/ptu/state` | `sensor_msgs/msg/JointState` | Eingang | Istposition der PTU |
| `/trigger` | `std_msgs/msg/Bool` | Ausgang/Eingang | Trigger-Signal vom Aim-Node zum Trigger-Node |
| `/ptu/reference` | `std_srvs/srv/Trigger` | Service | Startet die PTU-Referenzfahrt |

## Parameter

### `aim_and_fire`

| Parameter | Default | Einheit | Beschreibung |
|---|---:|---:|---|
| `offset_x` | `0.0` | m | X-Versatz zwischen Zielkoordinatensystem und PTU-Achse |
| `offset_y` | `0.0` | m | Y-Versatz zwischen Zielkoordinatensystem und PTU-Achse |
| `offset_z` | `0.545` | m | Höhe der PTU-Neigungsachse über Boden bzw. Referenzebene |
| `pan_joint` | `ptu_pan` | - | Joint-Name der Pan-Achse |
| `tilt_joint` | `ptu_tilt` | - | Joint-Name der Tilt-Achse |
| `tolerance_deg` | `0.3` | ° | Winkeltoleranz zum Auslösen des Triggers |
| `tilt_offset_deg` | `14.26` | ° | Mechanischer Offset der Tilt-Achse |
| `tool_offset_z` | `0.045` | m | Vertikaler Versatz der Düse zur PTU-Achse |
| `speed_deg_s` | `13.0` | °/s | Sollgeschwindigkeit der PTU-Achsen |
| `water_speed_m_s` | `11.8` | m/s | Geschwindigkeit des Wasserstrahls für die Fallkompensation |

### `trigger_node`

| Parameter | Default | Einheit | Beschreibung |
|---|---:|---:|---|
| `port` | `/dev/ttyACM0` | - | Serielle Schnittstelle des Mikrocontrollers |
| `baud_rate` | `9600` | Baud | Baudrate der seriellen Verbindung |

### `ptu_reference_node`

| Parameter | Default | Beschreibung |
|---|---:|---|
| `port` | `/dev/ttyUSB0` | Serielle Schnittstelle der PTU; alternativ über `PTU_PORT` setzbar |

## Beispiel: Zielpunkt publizieren

Ein einzelner Zielpunkt kann zum Testen über die Kommandozeile gesendet werden:

```bash
ros2 topic pub --once /target_point geometry_msgs/msg/Point "{x: 1.0, y: 2.0, z: 0.8}"
```

Der Aim-Node berechnet daraus Pan und Tilt, publiziert einen Befehl auf `/ptu/cmd` und wartet anschließend auf die passende Rückmeldung über `/ptu/state`. Bei Erreichen der Zielposition wird `/trigger` mit `true` publiziert.

## Serielle Schnittstellen prüfen

Verfügbare Geräte anzeigen:

```bash
ls -l /dev/ttyUSB* /dev/ttyACM*
```

Berechtigungen temporär setzen:

```bash
sudo chmod a+rw /dev/ttyUSB0
sudo chmod a+rw /dev/ttyACM0
```

Dauerhaft empfiehlt sich eine passende `udev`-Regel für PTU und Mikrocontroller.

## Kalibrierung

Vor dem produktiven Betrieb sollten die folgenden Werte experimentell bestimmt und in der Launch-Datei angepasst werden:

1. `offset_x`, `offset_y`, `offset_z`: Lage der PTU-Achse relativ zum Zielkoordinatensystem
2. `tilt_offset_deg`: mechanischer Nullpunktfehler der Tilt-Achse
3. `tool_offset_z`: Abstand zwischen PTU-Neigungsachse und Düse
4. `water_speed_m_s`: reale Austrittsgeschwindigkeit des Wasserstrahls
5. `tolerance_deg`: zulässige Winkeltoleranz vor Trigger-Auslösung
6. `speed_deg_s`: sichere Bewegungsgeschwindigkeit der PTU

## Troubleshooting

### Launch-Datei wird nicht gefunden

Prüfen, ob der Workspace gebaut und gesourced wurde:

```bash
colcon build
source install/setup.bash
ros2 pkg prefix aim_and_fire
```

### Keine Verbindung zur PTU

- Prüfen, ob `/dev/ttyUSB0` existiert
- Port über Parameter anpassen: `-p port:=/dev/ttyUSB1`
- Berechtigungen oder `udev`-Regeln prüfen
- Bei Docker-Betrieb sicherstellen, dass `/dev` in den Container gemountet ist und der Container privilegiert läuft

### Trigger wird nicht ausgelöst

- Prüfen, ob `/ptu/state` gültige Joint-Namen enthält: `ptu_pan` und `ptu_tilt`
- Prüfen, ob die Istposition innerhalb von `tolerance_deg` liegt
- Prüfen, ob der Mikrocontroller unter `/dev/ttyACM0` erreichbar ist
- Baudrate des Mikrocontrollers mit `baud_rate` abgleichen

### Docker startet falsche Launch-Datei

In `docker-compose.yml` ist der Startbefehl korrekt auf `aim_and_fire.launch.py` gesetzt. Falls der Container direkt über `docker run` gestartet wird, muss der `CMD` im Dockerfile angepasst werden:

```dockerfile
CMD ["bash", "-c", "source /opt/ros/jazzy/setup.bash && source /ros2_ws/install/setup.bash && ros2 launch aim_and_fire aim_and_fire.launch.py"]
```

## Lizenz

Das ROS-2-Package ist in `package.xml` mit `Apache-2.0` lizenziert.
