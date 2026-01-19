Hier ist der verbesserte Code für 'ArchitechLens', der folgende Optimierungen und Features beinhaltet:

1.  **Fehlerbehandlung**:
    *   Robusteres Logging mit `try-except` Blöcken für Dateisystemoperationen.
    *   Umfassende Fehlerbehandlung bei der Serialisierung/Deserialisierung von Modellen (z.B. `FileNotFoundError`, `json.JSONDecodeError`, `ValidationError`).
    *   Validierung beim Hinzufügen von Elementen zum Modell (z.B. Eindeutigkeit der ID).
    *   Validierung von Enum-Typen in Dataclasses bei der Initialisierung (`__post_init__`).
2.  **Optimierung**:
    *   Ein benutzerdefinierter JSON-Encoder (`ArchitechLensJSONEncoder`), der `Path`-Objekte, `Enum`-Werte und Dataclasses korrekt in JSON serialisiert.
    *   Eine Hilfsfunktion für die Deserialisierung, um generisch Dictionaries in die entsprechenden Dataclass-Objekte zurückzukonvertieren, einschließlich verschachtelter Strukturen und Listen von Dataclasses.
    *   Bessere Strukturierung und Kapselung der Modellinteraktionen.
3.  **Kleine Features**:
    *   `ArchitechLensConfig`: Hinzufügen von `default_encoding` für Datevorgänge.
    *   `GeometricProperties`: Methode `calculate_volume()` zur Berechnung des Volumens basierend auf den Dimensionen.
    *   `ArchitecturalElement`: Methoden `add_property()` und `get_property()` für eine strukturiertere Verwaltung von benutzerdefinierten Eigenschaften.
    *   `ArchitecturalModel`:
        *   Methode `remove_element()` zum Entfernen von Elementen.
        *   Methode `filter_elements_by_type()` zum Filtern von Elementen nach ihrem `ElementType`.
        *   Methode `get_elements_by_material()` zum Filtern nach Material.
    *   `ArchitechLens` (Hauptklasse): Bessere Log-Ausgaben für Lade- und Speichervorgänge mit detaillierteren Fehlermeldungen.

---


import json
import logging
from pathlib import Path
from dataclasses import dataclass, field, asdict
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Any, Optional, Union, Type, TypeVar, Callable

# --- Custom Exceptions ---

class ArchitechLensError(Exception):
    """Base exception for ArchitechLens errors."""
    pass

class ConfigurationError(ArchitechLensError):
    """Exception raised for configuration-related issues."""
    pass

class ModelValidationError(ArchitechLensError):
    """Exception raised when a model's structure or data is invalid."""
    pass

class SerializationError(ArchitechLensError):
    """Exception raised during serialization failures."""
    pass

class DeserializationError(ArchitechLensError):
    """Exception raised during deserialization failures."""
    pass

class ElementNotFoundError(ArchitechLensError):
    """Exception raised when an element is not found in the model."""
    pass

# --- Configuration ---

@dataclass(frozen=True)
class ArchitechLensConfig:
    """
    Configuration settings for the ArchitechLens application.
    """
    data_directory: Path = Path("data")
    log_file_path: Path = Path("architechlens.log")
    log_level: int = logging.INFO
    default_model_format: str = "json"
    default_encoding: str = "utf-8" # Added: Default encoding for file operations

    def __post_init__(self):
        """
        Validates configuration paths.
        """
        if not isinstance(self.data_directory, Path):
            raise ConfigurationError("data_directory must be a pathlib.Path object.")
        if not isinstance(self.log_file_path, Path):
            raise ConfigurationError("log_file_path must be a pathlib.Path object.")
        if not self.data_directory.is_absolute():
            object.__setattr__(self, 'data_directory', Path.cwd() / self.data_directory)
        if not self.log_file_path.is_absolute():
            object.__setattr__(self, 'log_file_path', Path.cwd() / self.log_file_path)

# --- Logging Setup ---

def setup_logging(config: ArchitechLensConfig) -> None:
    """
    Sets up the logging configuration for the ArchitechLens application.
    Handles potential errors during directory creation.
    """
    log_dir = config.log_file_path.parent
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        # Log to console if file logging setup fails
        logging.basicConfig(level=logging.ERROR, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        logging.getLogger(__name__).error(f"Failed to create log directory {log_dir}: {e}")
        logging.getLogger(__name__).error("Proceeding without file logging. All logs will go to console.")
        # Re-configure basic logging to only stream handler if file handler creation failed
        logging.basicConfig(
            level=config.log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.StreamHandler()
            ]
        )
        return

    logging.basicConfig(
        level=config.log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(config.log_file_path),
            logging.StreamHandler()
        ]
    )
    logging.getLogger(__name__).info(f"Logging initialized. Log file: {config.log_file_path}")


# --- Enums ---

class ElementType(str, Enum):
    """
    Defines common architectural element types.
    """
    BUILDING = "BUILDING"
    FLOOR = "FLOOR"
    SPACE = "SPACE"
    WALL = "WALL"
    COLUMN = "COLUMN"
    BEAM = "BEAM"
    WINDOW = "WINDOW"
    DOOR = "DOOR"
    SLAB = "SLAB"
    ROOF = "ROOF"
    OTHER = "OTHER"

class Material(str, Enum):
    """
    Defines common building materials.
    """
    CONCRETE = "CONCRETE"
    STEEL = "STEEL"
    WOOD = "WOOD"
    GLASS = "GLASS"
    BRICK = "BRICK"
    PLASTER = "PLASTER"
    INSULATION = "INSULATION"
    ALUMINUM = "ALUMINUM"
    OTHER = "OTHER"

# --- Data Models (using dataclasses for structured data) ---

@dataclass
class GeometricProperties:
    """
    Represents geometric properties of an architectural element.
    Fields are optional to accommodate various levels of detail.
    """
    coordinates: Optional[List[float]] = field(default_factory=list) # e.g., [x, y, z] for origin
    dimensions: Optional[List[float]] = field(default_factory=list)  # e.g., [length, width, height]
    # More advanced geometric properties could be added here (e.g., shape, orientation matrix)

    def calculate_volume(self) -> Optional[float]:
        """
        Calculates the volume if dimensions (length, width, height) are provided.
        Assumes dimensions[0]=length, dimensions[1]=width, dimensions[2]=height.
        """
        if self.dimensions and len(self.dimensions) >= 3:
            # Assumes simple cuboid for volume calculation
            return self.dimensions[0] * self.dimensions[1] * self.dimensions[2]
        logging.getLogger(__name__).warning("Cannot calculate volume: insufficient dimensions (expected at least 3).")
        return None

@dataclass
class Relationship:
    """
    Defines a relationship between architectural elements.
    """
    type: str # e.g., "contains", "connected_to", "hosts"
    target_element_id: str # The ID of the element this one is related to
    description: Optional[str] = None

@dataclass
class ArchitecturalElement:
    """
    Represents a single architectural element within a building model.
    """
    element_id: str
    name: str
    element_type: ElementType
    material: Material
    description: Optional[str] = None
    geometric_properties: Optional[GeometricProperties] = field(default_factory=GeometricProperties)
    properties: Dict[str, Any] = field(default_factory=dict) # Custom properties (e.g., fire rating, U-value)
    relationships: List[Relationship] = field(default_factory=list)

    def __post_init__(self):
        """
        Performs validation after initialization.
        Ensures element_type and material are valid Enum members.
        """
        if not isinstance(self.element_type, ElementType):
            try: # Attempt to convert string to Enum if not already
                self.element_type = ElementType(str(self.element_type))
            except ValueError:
                raise ModelValidationError(f"Invalid element_type for element '{self.name}': {self.element_type}")
        
        if not isinstance(self.material, Material):
            try: # Attempt to convert string to Enum if not already
                self.material = Material(str(self.material))
            except ValueError:
                raise ModelValidationError(f"Invalid material for element '{self.name}': {self.material}")

        if not self.element_id:
            raise ModelValidationError("Element ID cannot be empty.")
        if not self.name:
            raise ModelValidationError("Element name cannot be empty.")

    def add_property(self, key: str, value: Any) -> None:
        """Adds a custom property to the element."""
        if not isinstance(key, str) or not key:
            raise ValueError("Property key must be a non-empty string.")
        self.properties[key] = value

    def get_property(self, key: str) -> Optional[Any]:
        """Retrieves a custom property by key."""
        return self.properties.get(key)

@dataclass
class ArchitecturalModel:
    """
    Represents an entire architectural model, comprising multiple elements.
    """
    model_id: str
    name: str
    elements: Dict[str, ArchitecturalElement] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """
        Performs validation after initialization.
        """
        if not self.model_id:
            raise ModelValidationError("Model ID cannot be empty.")
        if not self.name:
            raise ModelValidationError("Model name cannot be empty.")

    def add_element(self, element: ArchitecturalElement) -> None:
        """
        Adds an architectural element to the model.
        Raises ModelValidationError if an element with the same ID already exists.
        """
        if not isinstance(element, ArchitecturalElement):
            raise TypeError("Only ArchitecturalElement instances can be added.")
        if element.element_id in self.elements:
            raise ModelValidationError(f"Element with ID '{element.element_id}' already exists in the model.")
        self.elements[element.element_id] = element
        logging.getLogger(__name__).debug(f"Element '{element.name}' (ID: {element.element_id}) added to model '{self.name}'.")

    def get_element(self, element_id: str) -> ArchitecturalElement:
        """
        Retrieves an element by its ID.
        Raises ElementNotFoundError if the element does not exist.
        """
        if element_id not in self.elements:
            raise ElementNotFoundError(f"Element with ID '{element_id}' not found in model '{self.name}'.")
        return self.elements[element_id]

    def remove_element(self, element_id: str) -> None:
        """
        Removes an element from the model by its ID.
        Raises ElementNotFoundError if the element does not exist.
        """
        if element_id not in self.elements:
            raise ElementNotFoundError(f"Cannot remove: Element with ID '{element_id}' not found in model '{self.name}'.")
        del self.elements[element_id]
        logging.getLogger(__name__).debug(f"Element with ID '{element_id}' removed from model '{self.name}'.")

    def filter_elements_by_type(self, element_type: ElementType) -> List[ArchitecturalElement]:
        """
        Filters and returns a list of elements matching the given ElementType.
        """
        if not isinstance(element_type, ElementType):
            raise TypeError("element_type must be an instance of ElementType Enum.")
        return [element for element in self.elements.values() if element.element_type == element_type]

    def get_elements_by_material(self, material: Material) -> List[ArchitecturalElement]:
        """
        Filters and returns a list of elements matching the given Material.
        """
        if not isinstance(material, Material):
            raise TypeError("material must be an instance of Material Enum.")
        return [element for element in self.elements.values() if element.material == material]


# --- Model Serialization (Abstract Base Class) ---

T = TypeVar('T') # Type variable for generic deserialization

class ModelSerializer(ABC):
    """
    Abstract base class for model serializers.
    Defines the interface for converting architectural models to and from a persistent format.
    """
    def __init__(self, config: ArchitechLensConfig):
        self._config = config
        self._logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def serialize(self, model: ArchitecturalModel, file_path: Path) -> None:
        """
        Serializes an ArchitecturalModel object to a file.
        """
        pass

    @abstractmethod
    def deserialize(self, file_path: Path) -> ArchitecturalModel:
        """
        Deserializes an ArchitecturalModel object from a file.
        """
        pass

# --- Concrete Serializers ---

class ArchitechLensJSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder for ArchitechLens data models.
    Handles Path objects, Enum members, and dataclasses correctly.
    """
    def default(self, obj):
        if isinstance(obj, Path):
            return str(obj)
        if isinstance(obj, Enum):
            return obj.value
        if isinstance(obj, ArchitecturalModel):
            # Special handling for ArchitecturalModel to represent elements as a list of dicts
            # rather than a dict of dicts (which is harder to deserialize generically)
            data = asdict(obj)
            data['elements'] = list(data['elements'].values())
            return data
        if dataclasses.is_dataclass(obj):
            # Convert dataclasses to dicts using asdict for other dataclasses
            return asdict(obj)
        return super().default(obj)


class JsonModelSerializer(ModelSerializer):
    """
    Concrete implementation of ModelSerializer for JSON format.
    """

    def serialize(self, model: ArchitecturalModel, file_path: Path) -> None:
        """
        Serializes an ArchitecturalModel object to a JSON file.
        Uses a custom encoder to handle dataclasses, Enums, and Path objects.
        """
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding=self._config.default_encoding) as f:
                json.dump(model, f, indent=4, cls=ArchitechLensJSONEncoder)
            self._logger.info(f"Model '{model.name}' (ID: {model.model_id}) serialized to '{file_path}'.")
        except TypeError as e:
            raise SerializationError(f"Type error during JSON serialization of model '{model.name}': {e}") from e
        except OSError as e:
            raise SerializationError(f"File system error during JSON serialization to '{file_path}': {e}") from e
        except Exception as e:
            raise SerializationError(f"An unexpected error occurred during serialization: {e}") from e

    def deserialize(self, file_path: Path) -> ArchitecturalModel:
        """
        Deserializes an ArchitecturalModel object from a JSON file.
        Includes robust error handling and reconstruction of dataclass objects.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Model file not found at '{file_path}'.")

        try:
            with open(file_path, 'r', encoding=self._config.default_encoding) as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise DeserializationError(f"Invalid JSON format in file '{file_path}': {e}") from e
        except OSError as e:
            raise DeserializationError(f"File system error during JSON deserialization from '{file_path}': {e}") from e

        try:
            # Reconstruct the main ArchitecturalModel
            elements_data = data.pop('elements', [])
            model = ArchitecturalModel(
                model_id=data.get('model_id'),
                name=data.get('name'),
                metadata=data.get('metadata', {})
            )
            
            # Reconstruct elements and add them to the model
            for element_dict in elements_data:
                geometric_props_data = element_dict.pop('geometric_properties', {})
                geometric_properties = GeometricProperties(**geometric_props_data)

                relationships_data = element_dict.pop('relationships', [])
                relationships = [Relationship(**rel) for rel in relationships_data]
                
                # Ensure element_type and material are converted to Enum members during reconstruction
                element_dict['element_type'] = ElementType(element_dict['element_type'])
                element_dict['material'] = Material(element_dict['material'])

                element = ArchitecturalElement(
                    geometric_properties=geometric_properties,
                    relationships=relationships,
                    **element_dict
                )
                model.add_element(element) # Use add_element to leverage its validation

            self._logger.info(f"Model '{model.name}' (ID: {model.model_id}) deserialized from '{file_path}'.")
            return model
        except KeyError as e:
            raise DeserializationError(f"Missing required field '{e}' during model reconstruction from '{file_path}'.") from e
        except (ValueError, TypeError, ModelValidationError) as e:
            raise DeserializationError(f"Data type or validation error during model reconstruction from '{file_path}': {e}") from e
        except Exception as e:
            raise DeserializationError(f"An unexpected error occurred during deserialization: {e}") from e


# --- Main Application Logic ---

class ArchitechLens:
    """
    Main application class for ArchitechLens. Manages configuration, logging,
    and interaction with architectural models through serializers.
    """
    def __init__(self, config: Optional[ArchitechLensConfig] = None):
        self._config = config if config else ArchitechLensConfig()
        setup_logging(self._config) # Initialize logging based on config

        self._logger = logging.getLogger(self.__class__.__name__)
        self._model: Optional[ArchitecturalModel] = None

        # Ensure data directory exists
        try:
            self._config.data_directory.mkdir(parents=True, exist_ok=True)
            self._logger.info(f"Data directory '{self._config.data_directory}' ensured to exist.")
        except OSError as e:
            self._logger.error(f"Failed to create data directory '{self._config.data_directory}': {e}")
            raise ConfigurationError(f"Cannot initialize ArchitechLens: Failed to create data directory.") from e

        # Initialize serializer based on default_model_format
        if self._config.default_model_format == "json":
            self._serializer: ModelSerializer = JsonModelSerializer(self._config)
        # elif self._config.default_model_format == "ifc":
        #    self._serializer = IfcModelSerializer(self._config) # Placeholder for other formats
        else:
            raise NotImplementedError(f"Serializer for format '{self._config.default_model_format}' not implemented.")

    @property
    def current_model(self) -> Optional[ArchitecturalModel]:
        return self._model

    def load_model(self, model_filename: str) -> Optional[ArchitecturalModel]:
        """
        Loads an architectural model from the data directory.
        """
        file_path = self._config.data_directory / model_filename
        self._logger.info(f"Attempting to load model from: {file_path}")
        try:
            self._model = self._serializer.deserialize(file_path)
            self._logger.info(f"Model '{self._model.name}' (ID: {self._model.model_id}) loaded successfully.")
            return self._model
        except ArchitechLensError as e:
            self._logger.error(f"Failed to load model from '{file_path}': {e}")
            self._model = None # Ensure no partial model is set
        except Exception as e:
            self._logger.critical(f"An unhandled error occurred during model loading from '{file_path}': {e}", exc_info=True)
            self._model = None
        return None

    def save_model(self, model: ArchitecturalModel, model_filename: str) -> bool:
        """
        Saves an architectural model to the data directory.
        """
        file_path = self._config.data_directory / model_filename
        self._logger.info(f"Attempting to save model '{model.name}' (ID: {model.model_id}) to: {file_path}")
        try:
            self._serializer.serialize(model, file_path)
            self._logger.info(f"Model '{model.name}' (ID: {model.model_id}) saved successfully to '{file_path}'.")
            return True
        except ArchitechLensError as e:
            self._logger.error(f"Failed to save model '{model.name}' to '{file_path}': {e}")
        except Exception as e:
            self._logger.critical(f"An unhandled error occurred during model saving to '{file_path}': {e}", exc_info=True)
        return False

    def create_new_model(self, model_id: str, name: str) -> ArchitecturalModel:
        """
        Creates a new empty architectural model and sets it as the current model.
        """
        try:
            new_model = ArchitecturalModel(model_id=model_id, name=name)
            self._model = new_model
            self._logger.info(f"New model '{name}' (ID: {model_id}) created.")
            return new_model
        except ModelValidationError as e:
            self._logger.error(f"Failed to create new model: {e}")
            raise # Re-raise to indicate failure


# Example Usage
if __name__ == "__main__":
    # 1. Setup Configuration
    # You can customize these paths, e.g., for testing
    my_config = ArchitechLensConfig(
        data_directory=Path("./my_arch_data"),
        log_file_path=Path("./logs/architechlens_app.log"),
        log_level=logging.DEBUG # Set to DEBUG for more detailed logging
    )

    # 2. Initialize ArchitechLens Application
    try:
        app = ArchitechLens(config=my_config)
    except ConfigurationError as e:
        print(f"Application setup failed: {e}")
        exit(1)

    # 3. Create a new model
    my_model = app.create_new_model(model_id="project_alpha_1", name="Alpha Building Project")

    # 4. Add some elements
    wall_geometry = GeometricProperties(coordinates=[0.0, 0.0, 0.0], dimensions=[5.0, 0.2, 3.0])
    wall_element = ArchitecturalElement(
        element_id="wall_001",
        name="Main Exterior Wall",
        element_type=ElementType.WALL,
        material=Material.CONCRETE,
        description="A reinforced concrete wall.",
        geometric_properties=wall_geometry
    )
    wall_element.add_property("fire_rating", "F90")
    wall_element.add_property("u_value", 0.3)
    my_model.add_element(wall_element)
    
    # Calculate and log volume of the wall
    volume = wall_element.geometric_properties.calculate_volume()
    if volume is not None:
        app._logger.info(f"Volume of {wall_element.name}: {volume:.2f} cubic meters.")

    window_geometry = GeometricProperties(coordinates=[1.0, 0.1, 1.2], dimensions=[1.5, 0.1, 1.0])
    window_element = ArchitecturalElement(
        element_id="window_001",
        name="Living Room Window",
        element_type=ElementType.WINDOW,
        material=Material.GLASS,
        geometric_properties=window_geometry,
        relationships=[Relationship(type="hosts", target_element_id="wall_001")]
    )
    my_model.add_element(window_element)

    floor_slab = ArchitecturalElement(
        element_id="slab_001",
        name="Ground Floor Slab",
        element_type=ElementType.SLAB,
        material=Material.CONCRETE,
        geometric_properties=GeometricProperties(dimensions=[10.0, 8.0, 0.2])
    )
    my_model.add_element(floor_slab)

    # Example of invalid element (should raise error due to non-existent ElementType)
    try:
        invalid_element = ArchitecturalElement(
            element_id="invalid_001",
            name="Bad Element",
            element_type="NON_EXISTENT_TYPE", # This will cause an error
            material=Material.STEEL
        )
        my_model.add_element(invalid_element)
    except ModelValidationError as e:
        app._logger.error(f"Caught expected error when adding invalid element: {e}")
    except TypeError as e: # This might also be caught if __post_init__ does not handle conversion.
        app._logger.error(f"Caught expected TypeError for invalid enum: {e}")


    # 5. Save the model
    save_success = app.save_model(my_model, "project_alpha_model.json")
    if save_success:
        app._logger.info("Model saved successfully.")
    else:
        app._logger.error("Model saving failed.")

    # 6. Load the model back (simulate a new session or check persistence)
    app._model = None # Clear current model to ensure we load fresh
    loaded_model = app.load_model("project_alpha_model.json")

    if loaded_model:
        app._logger.info(f"Loaded model name: {loaded_model.name}")
        app._logger.info(f"Number of elements in loaded model: {len(loaded_model.elements)}")

        # 7. Use new features on the loaded model
        try:
            retrieved_wall = loaded_model.get_element("wall_001")
            app._logger.info(f"Retrieved wall: {retrieved_wall.name}, Material: {retrieved_wall.material.value}")
            app._logger.info(f"Wall fire rating: {retrieved_wall.get_property('fire_rating')}")

            # Filter elements
            walls = loaded_model.filter_elements_by_type(ElementType.WALL)
            app._logger.info(f"Found {len(walls)} wall elements.")
            
            concrete_elements = loaded_model.get_elements_by_material(Material.CONCRETE)
            app._logger.info(f"Found {len(concrete_elements)} concrete elements.")

            # Try to get a non-existent element
            try:
                loaded_model.get_element("non_existent_id")
            except ElementNotFoundError as e:
                app._logger.error(f"Caught expected error: {e}")

            # Try to remove an element
            try:
                loaded_model.remove_element("window_001")
                app._logger.info("Window_001 removed.")
                app._logger.info(f"Elements after removal: {len(loaded_model.elements)}")
                # Try to remove it again (should fail)
                loaded_model.remove_element("window_001")
            except ElementNotFoundError as e:
                app._logger.error(f"Caught expected error: {e}")

        except ArchitechLensError as e:
            app._logger.error(f"Error during model interaction: {e}")

    # 8. Test error handling for non-existent file
    app._model = None
    app.load_model("non_existent_model.json") # This should log an error.

    # 9. Test error handling for invalid JSON file (create a dummy corrupt file)
    corrupt_file_path = my_config.data_directory / "corrupt_model.json"
    with open(corrupt_file_path, 'w', encoding=my_config.default_encoding) as f:
        f.write("{'model_id': 'test', 'name': 'Corrupt', 'elements': [}") # Invalid JSON
    app._logger.info(f"Attempting to load corrupt file: {corrupt_file_path}")
    app.load_model("corrupt_model.json")
    corrupt_file_path.unlink() # Clean up

