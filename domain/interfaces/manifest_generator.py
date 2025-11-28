from abc import ABC, abstractmethod
from models.operations.load import Load

class ManifestGenerator(ABC):
    @abstractmethod
    def generate(self, load: Load, load_data: dict) -> bytes:
        """
        Generates a manifest document for the given load.
        Returns the binary content of the document (e.g., PDF bytes).
        """
        pass
