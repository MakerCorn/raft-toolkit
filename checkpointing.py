from dataclasses import dataclass
from pathlib import Path
from typing import List
from datasets import Dataset, concatenate_datasets
import logging
import shutil

logger = logging.getLogger("raft")

@dataclass
class Checkpoint:
    """
    Represents a single checkpoint for a chunked dataset.

    Attributes:
        path (Path): Path to the checkpoint directory.
        num (int): Chunk/checkpoint number.
    """

    path: Path
    num: int

    def load(self) -> Dataset:
        """
        Load the dataset from this checkpoint.

        Returns:
            Dataset: The loaded dataset.
        """
        return Dataset.load_from_disk(self.path)

    def __lt__(self, other: 'Checkpoint') -> bool:
        """Compare checkpoints by chunk number (less than)."""
        return self.num < other.num

    def __eq__(self, other: 'Checkpoint') -> bool:
        """Check if two checkpoints are equal by chunk number."""
        return self.num == other.num

    def __hash__(self) -> int:
        """Hash checkpoint by chunk number."""
        return hash(self.num)

class Checkpointing:
    """
    Manages saving, loading, and collecting chunk checkpoints for datasets.
    """

    def __init__(self, checkpoints_dir: Path) -> None:
        """
        Args:
            checkpoints_dir (Path): Directory to store checkpoints.
        """
        self.checkpoints_dir = checkpoints_dir

    def missing_checkpoints(self, num) -> List[int]:
        """
        Returns a list of missing checkpoint indices up to num.

        Args:
            num (int): Total number of expected checkpoints.

        Returns:
            List[int]: Indices of missing checkpoints.
        """
        return [n for n in range(0, num) if not (self.checkpoints_dir / f"checkpoint-{n}").exists()]

    def save_checkpoint(self, ds: Dataset, num: int):
        """
        Save a dataset as a checkpoint.

        Args:
            ds (Dataset): Dataset to save.
            num (int): Chunk/checkpoint number.
        """
        checkpoint_path = self.checkpoints_dir / ("checkpoint-" + str(num))
        ds.save_to_disk(checkpoint_path)

    def load_checkpoint(self, num: int):
        """
        Load a checkpoint dataset if it exists.

        Args:
            num (int): Chunk/checkpoint number.

        Returns:
            Dataset or None: Loaded dataset or None if not found.
        """
        checkpoint_path = self.checkpoints_dir / ("checkpoint-" + str(num))
        if checkpoint_path.exists():
            return Dataset.load_from_disk(checkpoint_path)
        return None

    def get_checkpoints(self) -> List[Checkpoint]:
        """
        Get all available checkpoints in the directory.

        Returns:
            List[Checkpoint]: List of Checkpoint objects.
        """
        checkpoints = []
        for dir_path in self.checkpoints_dir.iterdir():
            if dir_path.is_dir() and dir_path.name.startswith("checkpoint-"):
                num = int(dir_path.name.split("-")[1])
                checkpoints.append(Checkpoint(dir_path, num))
        return checkpoints

    def collect_checkpoints(self) -> List[Dataset]:
        """
        Collect and concatenate all checkpoint datasets.

        Returns:
            Dataset: Concatenated dataset from all checkpoints.
        """
        ds_list = list([checkpoint.load() for checkpoint in self.get_checkpoints()])
        ds = concatenate_datasets(ds_list)
        return ds

    def delete_checkpoints(self):
        """
        Delete all checkpoints in the directory.
        """
        shutil.rmtree(self.checkpoints_dir)

def checkpointed(checkpointing: Checkpointing):
    """
    Decorator to wrap a function so that its results are checkpointed and loaded if available.

    Args:
        checkpointing (Checkpointing): The checkpointing manager instance.

    Returns:
        function: Wrapped function with checkpointing.
    """
    def wrapped(func):
        def wrapper(chunk_id, *args, **kwargs):
            ds = checkpointing.load_checkpoint(chunk_id)
            if ds:
                return ds
            ds = func(chunk_id=chunk_id, *args, **kwargs)
            checkpointing.save_checkpoint(ds, chunk_id)
            return ds
        return wrapper
    return wrapped