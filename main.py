Absolut! Hier ist der verbesserte Code für 'ArchitechLens', der alle von dir gewünschten Optimierungen, Features und umfassende Fehlerbehandlung beinhaltet.


import json
import logging
from pathlib import Path
from dataclasses import dataclass, field, asdict, is_dataclass
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Any, Optional, Type, TypeVar, get_origin, get_args

# --- Konfiguration ---
@dataclass
class ArchitechLensConfig:
    """
    Konfigurationsklasse für ArchitechLens.
    Definiert Standardeinstellungen wie Dateipfade und Kodierung.
    """
    default_encoding: str = "utf-8"
    model_directory: Path = Path("models")
    log_file: Path = Path("architechlens.log")
    log_level: int = logging.INFO

# --- Logging Setup ---
# Konfiguration des Loggings so früh wie möglich.
# Eine Instanz der Konfigurationsklasse wird für die initialen Einstellungen verwendet.
initial_config = ArchitechLensConfig()

# Sicherstellen, dass das Verzeichnis für die Logdatei existiert
initial_config.log_file.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=initial_config.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(initial_config.log_file, encoding=initial_config.default_encoding),
        logging.StreamHandler()  # Ausgabe auch auf der Konsole
    ]
)
logger = logging.getLogger("ArchitechLens")

# --- Benutzerdefinierte Exceptions ---
class ArchitechLensError(Exception):
    """Basisklasse für anwendungsspezifische Fehler."""
    pass

class ValidationError(ArchitechLensError):
    """Fehler, der bei der Validierung von Daten oder Objekten auftritt."""
    pass

class ElementNotFoundError(ArchitechLensError):
    """Fehler, wenn ein angefordertes Element nicht gefunden wird."""
    pass

class DuplicateElementError(ArchitechLensError):
    """Fehler, wenn versucht wird, ein Element mit einer bereits existierenden ID hinzuzufügen."""
    pass

# --- Enums ---
class ElementType(Enum):
    """Definiert die möglichen Typen von Architekturelementen."""
    BEAM = "Beam"
    WALL = "Wall"
    COLUMN = "Column"
    DOOR = "Door"
    WINDOW = "Window"
    SLAB = "Slab"
    ROOF = "Roof"
    # ... weitere Typen können hier hinzugefügt werden

    def __str__(self):
        return self.value

class MaterialType(Enum):
    """Definiert die möglichen Typen von Materialien."""
    CONCRETE = "Concrete"
    STEEL = "Steel"
    WOOD = "Wood"
    GLASS = "Glass"
    BRICK = "Brick"
    PLASTER = "Plaster"
    # ... weitere Materialien können hier hinzugefügt werden

    def __str__(self):
        return self.value

# --- Geometrische Eigenschaften ---
@dataclass
class GeometricProperties:
    """Repräsentiert die geometrischen Abmessungen eines Elements."""
    length: float
    width: float
    height: float

    def __post_init__(self):
        """Validierung nach der Initialisierung, um positive Abmessungen zu gewährleisten."""
        if not all(isinstance(dim, (int, float)) and dim > 0 for dim in [self.length, self.width, self.height]):
            raise ValidationError("Abmessungen (Länge, Breite, Höhe) müssen positive Zahlen sein.")

    def calculate_volume(self) -> float:
        """Berechnet das Volumen des Elements."""
        return self.length * self.width * self.height

# --- Abstrakte Basisklasse für Architekturelemente ---
@dataclass
class ArchitecturalElement(ABC):
    """
    Abstrakte Basisklasse für alle Architekturelemente.
    Definiert gemeinsame Attribute und eine Schnittstelle für spezifische Elementtypen.
    """
    id: str
    name: str
    element_type: ElementType
    material: MaterialType
    geometric_properties: GeometricProperties
    custom_properties: Dict[str, Any] = field(default_factory=dict)  # Für flexible, benutzerdefinierte Eigenschaften

    def __post_init__(self):
        """
        Validierung gemeinsamer Attribute nach der Initialisierung.
        Stellt sicher, dass grundlegende Felder korrekt sind und Enums verwendet werden.
        """
        if not self.id:
            raise ValidationError("Element-ID darf nicht leer sein.")
        if not self.name:
            raise ValidationError("Element-Name darf nicht leer sein.")
        if not isinstance(self.element_type, ElementType):
            raise ValidationError(f"Ungültiger ElementType: '{self.element_type}'. Muss ein Mitglied des ElementType-Enums sein.")
        if not isinstance(self.material, MaterialType):
            raise ValidationError(f"Ungültiges Material: '{self.material}'. Muss ein Mitglied des MaterialType-Enums sein.")
        if not isinstance(self.geometric_properties, GeometricProperties):
            raise ValidationError(f"Ungültige geometrische Eigenschaften. Muss eine Instanz von GeometricProperties sein.")

    @abstractmethod
    def describe(self) -> str:
        """
        Abstrakte Methode zur Beschreibung des Elements.
        Muss von Unterklassen implementiert werden.
        """
        pass

    def add_property(self, key: str, value: Any):
        """
        Fügt eine benutzerdefinierte Eigenschaft zum Element hinzu oder aktualisiert sie.
        """
        if not isinstance(key, str) or not key:
            raise ValidationError("Eigenschaftsschlüssel muss ein nicht-leerer String sein.")
        self.custom_properties[key] = value
        logger.debug(f"Eigenschaft '{key}' zu Element '{self.id}' hinzugefügt/aktualisiert.")

    def get_property(self, key: str) -> Optional[Any]:
        """
        Ruft den Wert einer benutzerdefinierten Eigenschaft ab.
        Gibt None zurück, wenn die Eigenschaft nicht existiert.
        """
        return self.custom_properties.get(key)

# --- Konkrete Architekturelemente ---
@dataclass
class Beam(ArchitecturalElement):
    """Repräsentiert einen Träger, abgeleitet von ArchitecturalElement."""
    element_type: ElementType = field(default=ElementType.BEAM, init=False) # Typ ist fest für diese Klasse

    def __post_init__(self):
        super().__post_init__()  # Basisklassen-Validierung aufrufen
        if self.element_type != ElementType.BEAM:
            # Diese Prüfung ist redundant, da element_type mit init=False festgesetzt wird,
            # aber sie dient als Beispiel für typspezifische Validierung.
            raise ValidationError(f"Beam-Element muss den ElementType '{ElementType.BEAM.value}' haben.")

    def describe(self) -> str:
        return (f"Träger (ID: {self.id}, Name: {self.name}, Material: {self.material.value}, "
                f"Abmessungen: {self.geometric_properties.length:.2f}x"
                f"{self.geometric_properties.width:.2f}x"
                f"{self.geometric_properties.height:.2f}m)")

@dataclass
class Wall(ArchitecturalElement):
    """Repräsentiert eine Wand, abgeleitet von ArchitecturalElement."""
    element_type: ElementType = field(default=ElementType.WALL, init=False) # Typ ist fest für diese Klasse

    def __post_init__(self):
        super().__post_init__()  # Basisklassen-Validierung aufrufen
        if self.element_type != ElementType.WALL:
            raise ValidationError(f"Wall-Element muss den ElementType '{ElementType.WALL.value}' haben.")

    def describe(self) -> str:
        return (f"Wand (ID: {self.id}, Name: {self.name}, Material: {self.material.value}, "
                f"Abmessungen: {self.geometric_properties.length:.2f}x"
                f"{self.geometric_properties.width:.2f}x"
                f"{self.geometric_properties.height:.2f}m)")

@dataclass
class Column(ArchitecturalElement):
    """Repräsentiert eine Säule, abgeleitet von ArchitecturalElement."""
    element_type: ElementType = field(default=ElementType.COLUMN, init=False) # Typ ist fest für diese Klasse

    def __post_init__(self):
        super().__post_init__()  # Basisklassen-Validierung aufrufen
        if self.element_type != ElementType.COLUMN:
            raise ValidationError(f"Column-Element muss den ElementType '{ElementType.COLUMN.value}' haben.")

    def describe(self) -> str:
        return (f"Säule (ID: {self.id}, Name: {self.name}, Material: {self.material.value}, "
                f"Abmessungen: {self.geometric_properties.length:.2f}x"
                f"{self.geometric_properties.width:.2f}x"
                f"{self.geometric_properties.height:.2f}m)")


# --- Architekturmodell ---
@dataclass
class ArchitecturalModel:
    """
    Verwaltet eine Sammlung von Architekturelementen innerhalb eines Modells.
    """
    name: str
    elements: Dict[str, ArchitecturalElement] = field(default_factory=dict)  # Elemente, indiziert nach ihrer ID

    def __post_init__(self):
        """Validierung nach der Initialisierung, um einen gültigen Modellnamen zu gewährleisten."""
        if not self.name:
            raise ValidationError("Modellname darf nicht leer sein.")
        # Sicherstellen, dass alle hinzugefügten Elemente gültig sind und die IDs korrekt sind
        for element_id, element in self.elements.items():
            if not isinstance(element, ArchitecturalElement):
                raise ValidationError(f"Element mit ID '{element_id}' ist keine gültige ArchitecturalElement-Instanz.")
            if element.id != element_id:
                raise ValidationError(f"Element-ID-Mismatch: Key '{element_id}' stimmt nicht mit Element-ID '{element.id}' überein.")

    def add_element(self, element: ArchitecturalElement):
        """
        Fügt ein Element zum Modell hinzu.
        Wirft DuplicateElementError, wenn die ID bereits existiert.
        """
        if not isinstance(element, ArchitecturalElement):
            raise ValidationError("Das hinzugefügte Objekt muss eine Instanz von ArchitecturalElement sein.")
        if element.id in self.elements:
            raise DuplicateElementError(f"Element mit ID '{element.id}' existiert bereits im Modell '{self.name}'.")
        self.elements[element.id] = element
        logger.info(f"Element '{element.name}' (ID: {element.id}) zum Modell '{self.name}' hinzugefügt.")

    def get_element(self, element_id: str) -> Optional[ArchitecturalElement]:
        """
        Ruft ein Element anhand seiner ID ab.
        Gibt None zurück, wenn das Element nicht gefunden wird.
        """
        return self.elements.get(element_id)

    def remove_element(self, element_id: str) -> ArchitecturalElement:
        """
        Entfernt ein Element anhand seiner ID aus dem Modell.
        Wirft ElementNotFoundError, wenn das Element nicht existiert.
        """
        if element_id not in self.elements:
            raise ElementNotFoundError(f"Element mit ID '{element_id}' nicht im Modell '{self.name}' gefunden.")
        removed_element = self.elements.pop(element_id)
        logger.info(f"Element '{removed_element.name}' (ID: {element_id}) aus Modell '{self.name}' entfernt.")
        return removed_element

    def filter_elements_by_type(self, element_type: ElementType) -> List[ArchitecturalElement]:
        """
        Filtert Elemente nach ihrem ElementType.
        """
        if not isinstance(element_type, ElementType):
            raise ValidationError(f"Ungültiger ElementType: '{element_type}'. Muss ein ElementType-Enum sein.")
        return [elem for elem in self.elements.values() if elem.element_type == element_type]

    def get_elements_by_material(self, material_type: MaterialType) -> List[ArchitecturalElement]:
        """
        Filtert Elemente nach ihrem MaterialType.
        """
        if not isinstance(material_type, MaterialType):
            raise ValidationError(f"Ungültiger MaterialType: '{material_type}'. Muss ein MaterialType-Enum sein.")
        return [elem for elem in self.elements.values() if elem.material == material_type]

# --- Benutzerdefinierter JSON Encoder/Decoder ---

class ArchitechLensJSONEncoder(json.JSONEncoder):
    """
    Ein benutzerdefinierter JSON-Encoder, der Path-Objekte, Enum-Werte und
    Dataclasses korrekt in JSON serialisiert.
    """
    def default(self, obj):
        if isinstance(obj, Path):
            return str(obj)
        if isinstance(obj, Enum):
            return obj.value
        if is_dataclass(obj):
            # asdict konvertiert alle Felder rekursiv in Dictionaries.
            # Der Encoder fängt dann die Basistypen wie Enum, Path etc. ab.
            return asdict(obj)
        return super().default(obj)

# Typvariable für die Deserialisierungsfunktion
T = TypeVar('T')

def _deserialize_dataclass(data: Dict[str, Any], target_class: Type[T]) -> T:
    """
    Hilfsfunktion, um ein Dictionary in eine Dataclass-Instanz zu deserialisieren.
    Behandelt verschachtelte Dataclasses, Listen von Dataclasses, Enums und Path-Objekte.
    Kann auch polymorphe Deserialisierung für eine abstrakte Basisklasse wie ArchitecturalElement durchführen.
    """
    if not is_dataclass(target_class) and target_class != ArchitecturalElement: # ArchitecturalElement ist ABC
        raise TypeError(f"Die Zielklasse muss eine Dataclass sein (oder ArchitecturalElement), aber erhielt {target_class}")
    if not isinstance(data, dict):
        raise TypeError(f"Daten müssen ein Dictionary sein, um in {target_class.__name__} zu deserialisieren, aber erhielt {type(data)}")

    # Mapping von ElementType-Werten zu den konkreten Klassen
    # Dies ist notwendig, da ArchitecturalElement eine abstrakte Klasse ist
    # und wir wissen müssen, welche konkrete Klasse (Beam, Wall, Column) instanziiert werden soll.
    element_type_class_map: Dict[str, Type[ArchitecturalElement]] = {
        ElementType.BEAM.value: Beam,
        ElementType.WALL.value: Wall,
        ElementType.COLUMN.value: Column,
        # ... weitere Mappings hinzufügen, falls weitere konkrete Elemente existieren
    }

    # Wenn die Zielklasse ArchitecturalElement ist, leiten wir die tatsächliche Klasse
    # vom 'element_type'-Feld im Daten-Dictionary ab, um die korrekte Unterklasse zu instanziieren.
    actual_target_class = target_class
    if target_class == ArchitecturalElement:
        element_type_value = data.get('element_type')
        if element_type_value is None:
            raise ValidationError("Kann ArchitecturalElement nicht deserialisieren: 'element_type' fehlt im Daten-Dictionary.")
        concrete_class = element_type_class_map.get(element_type_value)
        if concrete_class is None:
            raise ValidationError(f"Unbekannter ElementType '{element_type_value}' für die Deserialisierung.")
        actual_target_class = concrete_class

    field_values = {}
    # Iteriere über die Felder der (konkreten) Ziel-Dataclass
    for field_name, field_type in actual_target_class.__annotations__.items():
        if field_name not in data:
            # Wenn ein Feld nicht im Daten-Dict ist, aber einen Default-Wert hat,
            # wird es vom Dataclass-Konstruktor korrekt behandelt.
            # Für Felder ohne Default wird der Konstruktor Fehler werfen.
            continue

        value = data[field_name]
        origin = get_origin(field_type)  # Z.B. list, dict, Union (für Optional)
        args = get_args(field_type)      # Z.B. [str], [ArchitecturalElement]

        if origin is list:
            # Behandle Listen (z.B. List[Dataclass], List[Enum], List[Path])
            item_type = args[0]
            if is_dataclass(item_type) or (isinstance(item_type, type) and issubclass(item_type, Enum)):
                field_values[field_name] = [
                    _deserialize_dataclass(item_data, item_type) if is_dataclass(item_type) else item_type(item_data)
                    for item_data in value
                ]
            elif isinstance(item_type, type) and issubclass(item_type, Path):
                 field_values[field_name] = [Path(item_data) for item_data in value]
            else:
                field_values[field_name] = value  # Für Listen von Basistypen
        elif origin is dict:
            # Behandle Dictionaries (z.B. custom_properties).
            # Hier gehen wir davon aus, dass Schlüssel und Werte einfache Typen sind
            # oder dass die Werte flexibel sind (Any), wie bei custom_properties.
            field_values[field_name] = value
        elif origin is Optional:  # Entspricht Union[X, None]
            actual_type = args[0]
            if value is None:
                field_values[field_name] = None
            elif is_dataclass(actual_type):
                field_values[field_name] = _deserialize_dataclass(value, actual_type)
            elif isinstance(actual_type, type) and issubclass(actual_type, Enum):
                field_values[field_name] = actual_type(value)
            elif isinstance(actual_type, type) and issubclass(actual_type, Path):
                field_values[field_name] = Path(value)
            else:
                field_values[field_name] = value
        elif is_dataclass(field_type):
            # Behandle verschachtelte Dataclasses
            field_values[field_name] = _deserialize_dataclass(value, field_type)
        elif isinstance(field_type, type) and issubclass(field_type, Enum):
            # Behandle Enums
            try:
                field_values[field_name] = field_type(value)
            except ValueError as e:
                raise ValidationError(f"Fehler bei der Deserialisierung von Enum '{field_name}' mit Wert '{value}': {e}") from e
        elif isinstance(field_type, type) and issubclass(field_type, Path):
            # Behandle Path-Objekte
            field_values[field_name] = Path(value)
        else:
            # Basistypen (int, str, float, bool)
            field_values[field_name] = value

    # Instanziiere die (konkrete) Dataclass mit den vorbereiteten Werten
    try:
        return actual_target_class(**field_values)
    except TypeError as e:
        logger.error(f"Fehler beim Erstellen der Dataclass-Instanz {actual_target_class.__name__} mit Daten {field_values}: {e}")
        raise ValidationError(f"Fehler beim Instanziieren von {actual_target_class.__name__}: {e}") from e
    except ValidationError as e:
        logger.error(f"Validierungsfehler beim Erstellen der Dataclass-Instanz {actual_target_class.__name__}: {e}")
        raise


# --- Hauptklasse ArchitechLens ---
class ArchitechLens:
    """
    Die Hauptschnittstelle für die Verwaltung und Persistenz von Architekturelementen.
    """
    def __init__(self, config: Optional[ArchitechLensConfig] = None):
        self.config = config if config else ArchitechLensConfig()
        # Sicherstellen, dass das Verzeichnis für die Modelle existiert
        self.config.model_directory.mkdir(parents=True, exist_ok=True)
        self.current_model: Optional[ArchitecturalModel] = None
        logger.info("ArchitechLens-Instanz initialisiert.")

    def create_new_model(self, model_name: str) -> ArchitecturalModel:
        """
        Erstellt ein neues, leeres Architekturmodell und setzt es als aktuelles Modell.
        """
        try:
            new_model = ArchitecturalModel(name=model_name)
            self.current_model = new_model
            logger.info(f"Neues Modell '{model_name}' erstellt.")
            return new_model
        except ValidationError as e:
            logger.error(f"Fehler beim Erstellen eines neuen Modells '{model_name}': {e}")
            raise

    def load_model(self, model_name: str) -> ArchitecturalModel:
        """
        Lädt ein Architekturmodell aus einer JSON-Datei.
        Wirft FileNotFoundError, ArchitechLensError bei Ladefehlern.
        """
        file_path = self.config.model_directory / f"{model_name}.json"
        logger.info(f"Versuche Modell '{model_name}' von '{file_path}' zu laden...")

        if not file_path.is_file():
            logger.warning(f"Modell-Datei nicht gefunden: '{file_path}'.")
            self.current_model = None
            raise FileNotFoundError(f"Modell-Datei '{file_path}' existiert nicht.")

        try:
            with open(file_path, 'r', encoding=self.config.default_encoding) as f:
                data = json.load(f)

            # Deserialisiere das Hauptmodell (ArchitecturalModel)
            # Da 'elements' ein Dict[str, ArchitecturalElement] ist, müssen wir jedes Element
            # individuell über _deserialize_dataclass mit der polymorphen Logik deserialisieren.
            
            # _deserialize_dataclass kann das gesamte ArchitecturalModel-Objekt verarbeiten,
            # da es rekursiv ist und die enthaltenen Elemente korrekt deserialisieren kann.
            loaded_model = _deserialize_dataclass(data, ArchitecturalModel)
            
            self.current_model = loaded_model
            logger.info(f"Modell '{model_name}' erfolgreich geladen.")
            return self.current_model

        except FileNotFoundError: # Sollte oben schon abgefangen werden, aber zur Sicherheit
            logger.error(f"Laden fehlgeschlagen: Datei '{file_path}' nicht gefunden.")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Laden fehlgeschlagen: Ungültiges JSON-Format in '{file_path}': {e}")
            raise ArchitechLensError(f"Ungültiges JSON-Format in Modell-Datei '{file_path}': {e}") from e
        except ValidationError as e:
            logger.error(f"Laden fehlgeschlagen: Validierungsfehler beim Deserialisieren von Modell '{model_name}': {e}")
            raise ArchitechLensError(f"Modell-Validierungsfehler beim Laden von '{file_path}': {e}") from e
        except TypeError as e:
            logger.error(f"Laden fehlgeschlagen: Typfehler bei der Deserialisierung von Modell '{model_name}': {e}")
            raise ArchitechLensError(f"Typfehler beim Deserialisieren von '{file_path}': {e}") from e
        except Exception as e:
            logger.exception(f"Ein unerwarteter Fehler ist beim Laden von Modell '{model_name}' aus '{file_path}' aufgetreten.")
            raise ArchitechLensError(f"Unerwarteter Fehler beim Laden des Modells von '{file_path}': {e}") from e

    def save_model(self) -> bool:
        """
        Speichert das aktuell geladene Architekturmodell in eine JSON-Datei.
        Wirft ArchitechLensError bei Speicherfehlern.
        """
        if self.current_model is None:
            logger.warning("Kein Modell zum Speichern geladen. Speichervorgang abgebrochen.")
            return False

        model_name = self.current_model.name
        file_path = self.config.model_directory / f"{model_name}.json"
        logger.info(f"Speichere Modell '{model_name}' nach '{file_path}'...")

        try:
            # asdict() konvertiert das gesamte Dataclass-Objekt, einschliesslich verschachtelter
            # Dataclasses und Dictionaries, in ein Dictionary. Der benutzerdefinierte
            # ArchitechLensJSONEncoder fängt dann spezielle Typen wie Path und Enum ab.
            model_data = asdict(self.current_model)
            
            with open(file_path, 'w', encoding=self.config.default_encoding) as f:
                json.dump(model_data, f, cls=ArchitechLensJSONEncoder, indent=4)
            logger.info(f"Modell '{model_name}' erfolgreich gespeichert unter '{file_path}'.")
            return True
        except TypeError as e:
            logger.error(f"Speichern fehlgeschlagen: Typfehler bei der Serialisierung von Modell '{model_name}': {e}")
            raise ArchitechLensError(f"Serialisierungsfehler für Modell '{model_name}': {e}") from e
        except FileNotFoundError:
            # Dies sollte bei 'w' selten passieren, es sei denn, das Verzeichnis ist ungültig
            logger.error(f"Speichern fehlgeschlagen: Verzeichnis '{self.config.model_directory}' existiert nicht oder ist nicht beschreibbar.")
            raise ArchitechLensError(f"Datei- oder Verzeichnisfehler beim Speichern: '{file_path}'") from e
        except PermissionError as e:
            logger.error(f"Speichern fehlgeschlagen: Keine Berechtigung zum Schreiben in '{file_path}': {e}")
            raise ArchitechLensError(f"Berechtigungsfehler beim Speichern nach '{file_path}': {e}") from e
        except Exception as e:
            logger.exception(f"Ein unerwarteter Fehler ist beim Speichern von Modell '{model_name}' aufgetreten.")
            raise ArchitechLensError(f"Unerwarteter Fehler beim Speichern des Modells: {e}") from e

    def get_current_model(self) -> Optional[ArchitecturalModel]:
        """Gibt das aktuell geladene Modell zurück."""
        return self.current_model

# --- Beispielnutzung (Testen) ---
if __name__ == "__main__":
    logger.info("Starte ArchitechLens Beispielnutzung.")

    # 1. Konfiguration und Initialisierung der Hauptanwendung
    app = ArchitechLens()

    # 2. Neues Modell erstellen
    model_name = "MyFirstBuilding"
    try:
        model = app.create_new_model(model_name)
        logger.info(f"Aktuelles Modell: {model.name}")
    except ArchitechLensError as e:
        logger.critical(f"Kritischer Fehler beim Erstellen des Modells: {e}")
        exit(1)

    # 3. Elemente erstellen mit Validierungstests
    try:
        # Gültige Elemente
        beam1 = Beam(
            id="B001",
            name="Hauptträger EG",
            material=MaterialType.STEEL,
            geometric_properties=GeometricProperties(length=5.0, width=0.3, height=0.5)
        )
        beam1.add_property("fire_rating", "R60")
        beam1.add_property("supplier", "SteelCo")
        logger.info(f"Erstelltes Element: {beam1.describe()}")

        wall1 = Wall(
            id="W001",
            name="Aussenwand Nord",
            material=MaterialType.BRICK,
            geometric_properties=GeometricProperties(length=10.0, width=0.24, height=3.0)
        )
        wall1.add_property("u_value", 0.25)
        logger.info(f"Erstelltes Element: {wall1.describe()}")

        column1 = Column(
            id="C001",
            name="Stütze Empfang",
            material=MaterialType.CONCRETE,
            geometric_properties=GeometricProperties(length=0.4, width=0.4, height=3.0)
        )
        logger.info(f"Erstelltes Element: {column1.describe()}")

        # Test für negative Abmessungen (sollte ValidationError werfen)
        try:
            logger.info("Versuche, GeometricProperties mit negativen Abmessungen zu erstellen...")
            invalid_prop = GeometricProperties(length=-1.0, width=1.0, height=1.0)
        except ValidationError as e:
            logger.info(f"   Erwarteter Fehler abgefangen (GeometricProperties): {e}")

        # Test für ungültigen Enum-Typ (sollte ValidationError werfen)
        try:
            logger.info("Versuche, ein Beam-Element mit ungültigem MaterialType zu erstellen...")
            # Pylance/MyPy wird dies beim statischen Check bemängeln, aber zur Laufzeit testen wir die Validierung
            invalid_beam = Beam(
                id="B002",
                name="Invalid Beam",
                material="FakeMaterial" , # Hier absichtlich String statt MaterialType.
                geometric_properties=GeometricProperties(length=1.0, width=0.1, height=0.1)
            )
        except ValidationError as e:
            logger.info(f"   Erwarteter Fehler abgefangen (Enum-Typ): {e}")

    except ValidationError as e:
        logger.error(f"Fehler beim Erstellen von Elementen: {e}")
        exit(1)

    # 4. Elemente zum Modell hinzufügen mit Fehlerbehandlung
    try:
        model.add_element(beam1)
        model.add_element(wall1)
        model.add_element(column1)
        
        # Versuch, ein Element mit doppelter ID hinzuzufügen
        logger.info("Versuche, ein Element mit bereits existierender ID hinzuzufügen (sollte fehlschlagen)...")
        model.add_element(beam1)
    except DuplicateElementError as e:
        logger.info(f"   Erwarteter Fehler abgefangen (Duplikat): {e}")
    except ArchitechLensError as e:
        logger.error(f"Fehler beim Hinzufügen von Elementen zum Modell: {e}")
        exit(1)

    # 5. Elemente abrufen und beschreiben
    retrieved_wall = model.get_element("W001")
    if retrieved_wall:
        logger.info(f"Abgerufenes Element: {retrieved_wall.describe()}")
        logger.info(f"  Volumen der Wand: {retrieved_wall.geometric_properties.calculate_volume():.2f} m³")
        logger.info(f"  U-Wert der Wand (custom_property): {retrieved_wall.get_property('u_value')}")

    # 6. Elemente filtern
    beams_in_model = model.filter_elements_by_type(ElementType.BEAM)
    logger.info(f"Gefundene Träger ({ElementType.BEAM.value}): {[b.name for b in beams_in_model]}")

    concrete_elements = model.get_elements_by_material(MaterialType.CONCRETE)
    logger.info(f"Gefundene Betonelemente ({MaterialType.CONCRETE.value}): {[c.name for c in concrete_elements]}")

    # 7. Modell speichern
    try:
        if app.save_model():
            logger.info(f"Modell '{model_name}' erfolgreich gespeichert.")
        else:
            logger.warning(f"Modell '{model_name}' konnte nicht gespeichert werden.")
    except ArchitechLensError as e:
        logger.critical(f"Kritischer Fehler beim Speichern des Modells: {e}")
        exit(1)

    # 8. Neues ArchitechLens-Objekt erstellen und Modell laden
    logger.info("\n--- Teste Laden eines Modells mit neuer ArchitechLens-Instanz ---")
    app2 = ArchitechLens()
    try:
        loaded_model = app2.load_model(model_name)
        if loaded_model:
            logger.info(f"Modell '{loaded_model.name}' erfolgreich von app2 geladen.")
            
            loaded_beam = loaded_model.get_element("B001")
            if loaded_beam:
                logger.info(f"Geladener Träger: {loaded_beam.describe()}")
                logger.info(f"  Geladener Träger (fire_rating): {loaded_beam.get_property('fire_rating')}")
                logger.info(f"  Volumen des geladenen Trägers: {loaded_beam.geometric_properties.calculate_volume():.2f} m³")
                # Prüfen, ob der Typ (polymorph) korrekt deserialisiert wurde
                if isinstance(loaded_beam, Beam):
                    logger.info(f"  Typ '{Beam.__name__}' korrekt deserialisiert.")
                else:
                    logger.warning(f"  Typ '{Beam.__name__}' NICHT korrekt deserialisiert, ist stattdessen '{type(loaded_beam).__name__}'.")

            # Versuch, ein nicht-existierendes Element zu entfernen
            try:
                logger.info("Versuche, ein nicht-existierendes Element zu entfernen (sollte fehlschlagen)...")
                loaded_model.remove_element("NON_EXISTENT")
            except ElementNotFoundError as e:
                logger.info(f"   Erwarteter Fehler beim Entfernen abgefangen: {e}")

            # Element entfernen
            removed_elem = loaded_model.remove_element("C001")
            logger.info(f"Element entfernt: {removed_elem.name}")
            if not loaded_model.get_element("C001"):
                logger.info("Element 'C001' ist nicht mehr im Modell.")
            
            # Speichern des geänderten Modells
            logger.info("Speichere das geänderte Modell...")
            app2.save_model()

    except FileNotFoundError as e:
        logger.error(f"Datei nicht gefunden beim Laden: {e}")
        exit(1)
    except ArchitechLensError as e:
        logger.critical(f"Kritischer Fehler beim Laden oder Bearbeiten des Modells in app2: {e}")
        exit(1)

    # 9. Teste Laden eines nicht existierenden Modells
    logger.info("\n--- Teste Laden eines nicht existierenden Modells ---")
    app3 = ArchitechLens()
    try:
        app3.load_model("NonExistentModel")
    except FileNotFoundError as e:
        logger.info(f"Erwarteter Fehler beim Laden eines nicht existierenden Modells abgefangen: {e}")
    except ArchitechLensError as e:
        logger.error(f"Unerwarteter ArchitechLensError beim Laden eines nicht existierenden Modells: {e}")

    logger.info("ArchitechLens Beispielnutzung beendet.")

