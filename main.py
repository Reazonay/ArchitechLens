
import json
import logging
from pathlib import Path
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Any, Optional, Union, Type, TypeVar

# --- Configuration ---

@dataclass(frozen=True)
class ArchitechLensConfig:
    """
    Configuration settings for the ArchitechLens application.
    """
    data_directory: Path = Path("data")
    log_file_path: Path = Path("architechlens.log")
    log_level: int = logging.INFO
    default_model_format: str = "json" # Placeholder, could be 'ifc', 'obj', etc.

# --- Logging Setup ---

def setup_logging(config: ArchitechLensConfig) -> None:
    """
    Sets up the logging configuration for the ArchitechLens application.
    """
    log_dir = config.log_file_path.parent
    log_dir.mkdir(parents=True, exist_ok=True)

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
    Fields are optional to allow for varying levels of detail per element type.
    """
    length: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    thickness: Optional[float] = None
    area: Optional[float] = None
    volume: Optional[float] = None
    # Add more specific geometry, e.g., for bounding boxes, vertices, etc.
    # bounding_box: Optional[Tuple[Tuple[float, float, float], Tuple[float, float, float]]] = None

    def calculate_area_from_dimensions(self) -> Optional[float]:
        """Calculates area if length and width are available and area is not set."""
        if self.area is None and self.length is not None and self.width is not None:
            self.area = self.length * self.width
        return self.area

    def calculate_volume_from_dimensions(self) -> Optional[float]:
        """Calculates volume if area and height/thickness are available and volume is not set."""
        if self.volume is None:
            if self.area is not None and self.height is not None:
                self.volume = self.area * self.height
            elif self.length is not None and self.width is not None and self.thickness is not None:
                self.volume = self.length * self.width * self.thickness
        return self.volume

@dataclass
class ArchitecturalElement:
    """
    Base class for all architectural elements within a model.
    """
    id: str
    name: str
    type: ElementType
    material: Material
    properties: Dict[str, Any] = field(default_factory=dict)
    geometry: GeometricProperties = field(default_factory=GeometricProperties)
    parent_id: Optional[str] = None # For hierarchical models (e.g., Wall inside Floor)

    def __post_init__(self):
        """Perform post-initialization checks and calculations."""
        # Ensure enums are correctly assigned if string inputs are given
        if isinstance(self.type, str):
            self.type = ElementType(self.type.upper())
        if isinstance(self.material, str):
            self.material = Material(self.material.upper())

        # Attempt to calculate derived geometric properties if source data exists
        self.geometry.calculate_area_from_dimensions()
        self.geometry.calculate_volume_from_dimensions()

    def get_property(self, key: str, default: Any = None) -> Any:
        """Safely retrieve a property value."""
        return self.properties.get(key, default)

    def to_dict(self) -> Dict[str, Any]:
        """Converts the element to a dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "material": self.material.value,
            "properties": self.properties,
            "geometry": self.geometry.__dict__,
            "parent_id": self.parent_id
        }

# Specific element types (can be extended with specific fields if needed)
# For simplicity, they mostly just inherit and don't add new fields here,
# relying on `properties` and `geometry` for specific data.
@dataclass
class Building(ArchitecturalElement):
    """Represents a building element."""
    pass

@dataclass
class Floor(ArchitecturalElement):
    """Represents a floor element."""
    pass

@dataclass
class Space(ArchitecturalElement):
    """Represents an enclosed space."""
    pass

@dataclass
class Wall(ArchitecturalElement):
    """Represents a wall element."""
    pass

@dataclass
class Window(ArchitecturalElement):
    """Represents a window element."""
    pass

@dataclass
class ArchitecturalModel:
    """
    Represents an entire architectural model, containing a collection of elements
    and associated metadata.
    """
    name: str
    version: str
    date: str
    elements: List[ArchitecturalElement] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_element(self, element: ArchitecturalElement) -> None:
        """Adds an architectural element to the model."""
        self.elements.append(element)

    def get_element_by_id(self, element_id: str) -> Optional[ArchitecturalElement]:
        """Retrieves an element by its ID."""
        return next((e for e in self.elements if e.id == element_id), None)

    def to_dict(self) -> Dict[str, Any]:
        """Converts the model to a dictionary for serialization."""
        return {
            "metadata": {
                "name": self.name,
                "version": self.version,
                "date": self.date,
                **self.metadata
            },
            "elements": [element.to_dict() for element in self.elements]
        }

# --- Model Loaders (Abstract Base Class and Concrete Implementations) ---

T = TypeVar('T', bound=ArchitecturalElement)

class BaseModelLoader(ABC):
    """
    Abstract base class for architectural model loaders.
    Defines the interface for loading models from various data sources.
    """
    def __init__(self, element_map: Dict[ElementType, Type[ArchitecturalElement]]):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.element_map = element_map

    @abstractmethod
    def load_model(self, source: Union[Path, str]) -> ArchitecturalModel:
        """
        Loads an architectural model from the specified source.
        
        Args:
            source: The path or data source for the model.
        
        Returns:
            An ArchitecturalModel instance.
        """
        raise NotImplementedError

class JsonModelLoader(BaseModelLoader):
    """
    Loads an architectural model from a JSON file.
    """
    def __init__(self):
        super().__init__(element_map={
            ElementType.BUILDING: Building,
            ElementType.FLOOR: Floor,
            ElementType.SPACE: Space,
            ElementType.WALL: Wall,
            ElementType.WINDOW: Window,
            ElementType.DOOR: Door,
            ElementType.SLAB: ArchitecturalElement, # Default for others
            ElementType.COLUMN: ArchitecturalElement,
            ElementType.BEAM: ArchitecturalElement,
            ElementType.ROOF: ArchitecturalElement,
            ElementType.OTHER: ArchitecturalElement,
        })

    def load_model(self, file_path: Path) -> ArchitecturalModel:
        """
        Loads an architectural model from a JSON file.
        
        Args:
            file_path: The path to the JSON file.
        
        Returns:
            An ArchitecturalModel instance.
        
        Raises:
            FileNotFoundError: If the file does not exist.
            json.JSONDecodeError: If the file content is not valid JSON.
            ValueError: If the JSON structure is unexpected.
        """
        self.logger.info(f"Attempting to load model from JSON: {file_path}")
        if not file_path.exists():
            self.logger.error(f"JSON model file not found: {file_path}")
            raise FileNotFoundError(f"Model file not found: {file_path}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON format in {file_path}: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error reading JSON file {file_path}: {e}")
            raise

        try:
            metadata = data.get("metadata", {})
            model_name = metadata.get("name", "Unnamed Model")
            model_version = metadata.get("version", "1.0")
            model_date = metadata.get("date", "N/A")
            
            architectural_model = ArchitecturalModel(
                name=model_name,
                version=model_version,
                date=model_date,
                metadata=metadata
            )

            elements_data = data.get("elements", [])
            for elem_data in elements_data:
                try:
                    elem_type_str = elem_data.get("type", "OTHER").upper()
                    elem_type = ElementType(elem_type_str)
                    
                    element_class = self.element_map.get(elem_type, ArchitecturalElement)
                    
                    geometry_data = elem_data.get("geometry", {})
                    geometric_properties = GeometricProperties(**geometry_data)

                    element = element_class(
                        id=elem_data["id"],
                        name=elem_data.get("name", elem_data["id"]),
                        type=elem_type,
                        material=Material(elem_data.get("material", "OTHER").upper()),
                        properties=elem_data.get("properties", {}),
                        geometry=geometric_properties,
                        parent_id=elem_data.get("parent_id")
                    )
                    architectural_model.add_element(element)
                except KeyError as e:
                    self.logger.warning(f"Skipping element due to missing required key: {e} in {elem_data}")
                except ValueError as e:
                    self.logger.warning(f"Skipping element due to invalid enum value or data: {e} in {elem_data}")
                except Exception as e:
                    self.logger.error(f"Unexpected error processing element {elem_data.get('id', 'unknown')}: {e}")

            self.logger.info(f"Successfully loaded model '{architectural_model.name}' with {len(architectural_model.elements)} elements.")
            return architectural_model
        except Exception as e:
            self.logger.error(f"Error parsing model data structure from {file_path}: {e}", exc_info=True)
            raise ValueError(f"Failed to parse model structure from JSON: {e}")

# --- Model Analysis ---

class ModelAnalyzer:
    """
    Provides methods for analyzing an ArchitecturalModel.
    """
    def __init__(self, model: ArchitecturalModel):
        self.model = model
        self.logger = logging.getLogger(self.__class__.__name__)

    def calculate_total_area_by_type(self) -> Dict[ElementType, float]:
        """
        Calculates the total area for each element type in the model.
        Returns a dictionary where keys are ElementType and values are total areas.
        """
        total_areas: Dict[ElementType, float] = {}
        for element in self.model.elements:
            if element.geometry.area is not None:
                total_areas.setdefault(element.type, 0.0)
                total_areas[element.type] += element.geometry.area
            else:
                self.logger.debug(f"Element '{element.id}' ({element.name}) of type {element.type.value} has no defined area.")
        return total_areas

    def calculate_total_volume_by_material(self) -> Dict[Material, float]:
        """
        Calculates the total volume for each material type in the model.
        Returns a dictionary where keys are Material and values are total volumes.
        """
        total_volumes: Dict[Material, float] = {}
        for element in self.model.elements:
            if element.geometry.volume is not None:
                total_volumes.setdefault(element.material, 0.0)
                total_volumes[element.material] += element.geometry.volume
            else:
                self.logger.debug(f"Element '{element.id}' ({element.name}) of material {element.material.value} has no defined volume.")
        return total_volumes

    def count_elements_by_type(self) -> Dict[ElementType, int]:
        """
        Counts the number of elements for each type.
        """
        counts: Dict[ElementType, int] = {}
        for element in self.model.elements:
            counts.setdefault(element.type, 0)
            counts[element.type] += 1
        return counts

    def find_elements_with_property(self, property_key: str) -> List[ArchitecturalElement]:
        """
        Finds all elements that possess a specific property key.
        """
        return [elem for elem in self.model.elements if property_key in elem.properties]

# --- Model Filtering ---

class ModelFilter:
    """
    Provides methods for filtering architectural elements within a model.
    """
    def __init__(self, elements: List[ArchitecturalElement]):
        self.elements = elements
        self.logger = logging.getLogger(self.__class__.__name__)

    def filter_by_type(self, element_type: Union[ElementType, str]) -> List[ArchitecturalElement]:
        """Filters elements by a specific ElementType."""
        if isinstance(element_type, str):
            element_type = ElementType(element_type.upper())
        self.logger.debug(f"Filtering by type: {element_type.value}")
        return [elem for elem in self.elements if elem.type == element_type]

    def filter_by_material(self, material: Union[Material, str]) -> List[ArchitecturalElement]:
        """Filters elements by a specific Material."""
        if isinstance(material, str):
            material = Material(material.upper())
        self.logger.debug(f"Filtering by material: {material.value}")
        return [elem for elem in self.elements if elem.material == material]

    def filter_by_property_value(self, key: str, value: Any) -> List[ArchitecturalElement]:
        """Filters elements where a property matches a specific value."""
        self.logger.debug(f"Filtering by property '{key}' with value '{value}'")
        return [elem for elem in self.elements if elem.properties.get(key) == value]

    def filter_by_geometry_range(
        self,
        prop: str,  # e.g., 'area', 'volume', 'length'
        min_val: Optional[float] = None,
        max_val: Optional[float] = None
    ) -> List[ArchitecturalElement]:
        """
        Filters elements based on a range for a specific geometric property.
        """
        filtered_elements: List[ArchitecturalElement] = []
        for elem in self.elements:
            geo_val = getattr(elem.geometry, prop, None)
            if geo_val is not None:
                if (min_val is None or geo_val >= min_val) and \
                   (max_val is None or geo_val <= max_val):
                    filtered_elements.append(elem)
        self.logger.debug(f"Filtering by geometry '{prop}' in range [{min_val}, {max_val}] resulted in {len(filtered_elements)} elements.")
        return filtered_elements

# --- Report Generation ---

class ReportGenerator:
    """
    Generates various reports from architectural model data.
    """
    def __init__(self, model: ArchitecturalModel):
        self.model = model
        self.analyzer = ModelAnalyzer(model)
        self.logger = logging.getLogger(self.__class__.__name__)

    def generate_summary_report(self, output_path: Path) -> None:
        """
        Generates a comprehensive summary report for the model in markdown format.
        """
        self.logger.info(f"Generating summary report for '{self.model.name}' to {output_path}")

        total_elements = len(self.model.elements)
        elements_by_type = self.analyzer.count_elements_by_type()
        total_areas_by_type = self.analyzer.calculate_total_area_by_type()
        total_volumes_by_material = self.analyzer.calculate_total_volume_by_material()

        report_content = [
            f"# Architectural Model Summary Report: {self.model.name}",
            f"\n**Version:** {self.model.version}",
            f"**Date:** {self.model.date}",
            f"**Total Elements:** {total_elements}",
            f"\n## Element Counts by Type",
            "| Element Type | Count |",
            "|--------------|-------|"
        ]

        for elem_type, count in elements_by_type.items():
            report_content.append(f"| {elem_type.value.replace('_', ' ').title()} | {count} |")

        report_content.append("\n## Total Area by Element Type (m²)")
        report_content.append("| Element Type | Total Area (m²) |")
        report_content.append("|--------------|------------------|")
        for elem_type, area in total_areas_by_type.items():
            report_content.append(f"| {elem_type.value.replace('_', ' ').title()} | {area:,.2f} |")

        report_content.append("\n## Total Volume by Material (m³)")
        report_content.append("| Material | Total Volume (m³) |")
        report_content.append("|----------|-------------------|")
        for material, volume in total_volumes_by_material.items():
            report_content.append(f"| {material.value.replace('_', ' ').title()} | {volume:,.2f} |")

        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(report_content))
            self.logger.info(f"Summary report successfully generated to {output_path}")
        except IOError as e:
            self.logger.error(f"Error writing report to {output_path}: {e}")
            raise

# --- Main Application Class ---

class ArchitechLensApp:
    """
    The main application class for ArchitechLens, orchestrating
    model loading, analysis, filtering, and reporting.
    """
    def __init__(self, config: ArchitechLensConfig):
        self.config = config
        setup_logging(config)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.model: Optional[ArchitecturalModel] = None
        self._loader_map: Dict[str, BaseModelLoader] = {
            "json": JsonModelLoader()
            # Add other loaders here, e.g., "ifc": IfcModelLoader(), "obj": ObjModelLoader()
        }
        self.logger.info("ArchitechLens application initialized.")

    def load_model(self, model_file_name: str, model_format: Optional[str] = None) -> None:
        """
        Loads an architectural model from the specified file.
        """
        file_path = self.config.data_directory / model_file_name
        model_format = model_format or self.config.default_model_format

        loader = self._loader_map.get(model_format.lower())
        if not loader:
            self.logger.error(f"Unsupported model format: {model_format}")
            raise ValueError(f"No loader available for format: {model_format}")

        try:
            self.model = loader.load_model(file_path)
            self.logger.info(f"Model '{self.model.name}' loaded successfully.")
        except Exception as e:
            self.logger.critical(f"Failed to load model from {file_path}: {e}")
            self.model = None # Ensure model is reset on failure
            raise

    def analyze_model(self) -> ModelAnalyzer:
        """
        Returns a ModelAnalyzer instance for the currently loaded model.
        Raises ValueError if no model is loaded.
        """
        if not self.model:
            raise ValueError("No model loaded. Please load a model first.")
        return ModelAnalyzer(self.model)

    def filter_elements(self, elements: Optional[List[ArchitecturalElement]] = None) -> ModelFilter:
        """
        Returns a ModelFilter instance for the currently loaded model's elements,
        or a provided list of elements.
        Raises ValueError if no model is loaded and no elements are provided.
        """
        if elements is not None:
            return ModelFilter(elements)
        if not self.model:
            raise ValueError("No model loaded and no elements provided for filtering.")
        return ModelFilter(self.model.elements)

    def generate_report(self, output_file_name: str) -> None:
        """
        Generates a summary report for the currently loaded model.
        """
        if not self.model:
            raise ValueError("No model loaded. Cannot generate report.")
        
        report_path = self.config.data_directory / "reports" / output_file_name
        reporter = ReportGenerator(self.model)
        reporter.generate_summary_report(report_path)

    def run_example_workflow(self, model_file_name: str, report_file_name: str) -> None:
        """
        Demonstrates a typical workflow: load, analyze, filter, report.
        """
        self.logger.info(f"Starting example workflow with model '{model_file_name}'")
        try:
            # 1. Load Model
            self.load_model(model_file_name)

            if self.model:
                # 2. Analyze Model
                analyzer = self.analyze_model()
                total_areas = analyzer.calculate_total_area_by_type()
                self.logger.info(f"Total areas by type: {json.dumps({k.value: v for k, v in total_areas.items()}, indent=2)}")

                total_volumes = analyzer.calculate_total_volume_by_material()
                self.logger.info(f"Total volumes by material: {json.dumps({k.value: v for k, v in total_volumes.items()}, indent=2)}")

                # 3. Filter Elements
                wall_elements = self.filter_elements().filter_by_type(ElementType.WALL)
                self.logger.info(f"Found {len(wall_elements)} wall elements.")
                
                concrete_elements = self.filter_elements(wall_elements).filter_by_material(Material.CONCRETE)
                self.logger.info(f"Found {len(concrete_elements)} concrete wall elements.")

                large_walls = self.filter_elements(wall_elements).filter_by_geometry_range('area', min_val=20.0)
                self.logger.info(f"Found {len(large_walls)} walls with area >= 20.0 m².")

                # 4. Generate Report
                self.generate_report(report_file_name)
                
            self.logger.info("Example workflow completed successfully.")

        except Exception as e:
            self.logger.error(f"Example workflow failed: {e}", exc_info=True)

# --- Example Usage (requires a dummy JSON data file) ---

def create_dummy_model_json(file_path: Path):
    """
    Creates a dummy JSON file representing an architectural model for testing.
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)
    dummy_data = {
        "metadata": {
            "name": "ArchitechLens Demo Building",
            "version": "1.0",
            "date": "2023-10-27",
            "project_id": "AL-DEMO-001"
        },
        "elements": [
            {
                "id": "b_001",
                "name": "Main Building",
                "type": "BUILDING",
                "material": "OTHER",
                "properties": {"year_built": 2023},
                "geometry": {"area": 300.0, "height": 10.0, "volume": 3000.0}
            },
            {
                "id": "f_001",
                "name": "Ground Floor",
                "type": "FLOOR",
                "material": "CONCRETE",
                "properties": {"level": 0},
                "geometry": {"area": 100.0, "thickness": 0.3, "volume": 30.0},
                "parent_id": "b_001"
            },
            {
                "id": "f_002",
                "name": "First Floor",
                "type": "FLOOR",
                "material": "CONCRETE",
                "properties": {"level": 1},
                "geometry": {"area": 100.0, "thickness": 0.3, "volume": 30.0},
                "parent_id": "b_001"
            },
            {
                "id": "w_ext_001",
                "name": "Exterior Wall North",
                "type": "WALL",
                "material": "BRICK",
                "properties": {"fire_rating": "F90", "u_value": 0.25},
                "geometry": {"length": 10.0, "height": 3.0, "thickness": 0.3, "area": 30.0, "volume": 9.0},
                "parent_id": "f_001"
            },
            {
                "id": "w_ext_002",
                "name": "Exterior Wall South",
                "type": "WALL",
                "material": "BRICK",
                "properties": {"fire_rating": "F90", "u_value": 0.25},
                "geometry": {"length": 10.0, "height": 3.0, "thickness": 0.3, "area": 30.0, "volume": 9.0},
                "parent_id": "f_001"
            },
            {
                "id": "w_int_001",
                "name": "Interior Wall Main",
                "type": "WALL",
                "material": "PLASTER",
                "properties": {"sound_rating_db": 45},
                "geometry": {"length": 5.0, "height": 3.0, "thickness": 0.1, "area": 15.0, "volume": 1.5},
                "parent_id": "f_001"
            },
            {
                "id": "w_int_002",
                "name": "Interior Wall Office",
                "type": "WALL",
                "material": "WOOD",
                "properties": {"sound_rating_db": 30},
                "geometry": {"length": 3.0, "height": 3.0, "thickness": 0.1, "area": 9.0, "volume": 0.9},
                "parent_id": "f_001"
            },
            {
                "id": "win_001",
                "name": "Main Window",
                "type": "WINDOW",
                "material": "GLASS",
                "properties": {"glazing_type": "double", "frame_material": "aluminum"},
                "geometry": {"width": 2.0, "height": 1.5, "area": 3.0},
                "parent_id": "w_ext_001"
            },
            {
                "id": "space_office",
                "name": "Office Space 101",
                "type": "SPACE",
                "material": "OTHER",
                "properties": {"occupancy_load": 4},
                "geometry": {"area": 25.0, "height": 2.8, "volume": 70.0},
                "parent_id": "f_001"
            },
            {
                "id": "space_corridor",
                "name": "Corridor Ground",
                "type": "SPACE",
                "material": "OTHER",
                "properties": {"fire_zone": "A"},
                "geometry": {"area": 15.0, "height": 2.8, "volume": 42.0},
                "parent_id": "f_001"
            },
            {
                "id": "column_001",
                "name": "Support Column A1",
                "type": "COLUMN",
                "material": "CONCRETE",
                "properties": {"structural_load_kn": 150},
                "geometry": {"length": 0.4, "width": 0.4, "height": 3.0, "volume": 0.48}, # area assumed to be base area
                "parent_id": "f_001"
            }
        ]
    }

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(dummy_data, f, indent=2)
    logging.getLogger(__name__).info(f"Dummy model JSON created at: {file_path}")


if __name__ == "__main__":
    # Define configuration
    config = ArchitechLensConfig(
        data_directory=Path("./architechlens_data"),
        log_file_path=Path("./architechlens_data/logs/app.log"),
        log_level=logging.DEBUG
    )

    # Create dummy data file for demonstration
    dummy_model_file = config.data_directory / "demo_model.json"
    create_dummy_model_json(dummy_model_file)

    # Initialize and run the application
    app = ArchitechLensApp(config)
    app.run_example_workflow(
        model_file_name="demo_model.json",
        report_file_name="summary_report.md"
    )

    print(f"\n--- ArchitechLens Demo Complete ---")
    print(f"Check '{config.data_directory}/logs/app.log' for detailed logs.")
    print(f"Check '{config.data_directory}/reports/summary_report.md' for the generated report.")
    print(f"Example data is located in '{config.data_directory}'.")
