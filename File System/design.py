"""File System implementation."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict


# ─── Abstract Base Class (Composite Pattern) ──────────────────

@dataclass
class FileSystemNode(ABC):
    """Base node in a composite file-system tree."""
    name: str
    last_modified: datetime = field(default_factory=datetime.now)
    created_at: datetime = field(default_factory=datetime.now)
    children: Dict[str, 'FileSystemNode'] = field(default_factory=dict)

    @abstractmethod
    def isFile(self) -> bool:
        pass

    def addChild(self, name: str, child: 'FileSystemNode') -> None:
        self.children[name] = child
        self.last_modified = datetime.now()

    def getChild(self, name: str) -> 'FileSystemNode':
        return self.children.get(name, None)

    def deleteChild(self, name: str) -> None:
        if name not in self.children:
            raise ValueError(f"Child '{name}' does not exist")
        self.children.pop(name)


# ─── Concrete Implementations ─────────────────────────────────

@dataclass
class File(FileSystemNode):
    """Leaf node representing a file with content."""
    content: str = field(default_factory=str)
    extension: str = field(default_factory=str)

    def isFile(self) -> bool:
        return True

    def readContent(self) -> str:
        return self.content

    def writeContent(self, content: str) -> None:
        self.content = content
        self.last_modified = datetime.now()


@dataclass
class Directory(FileSystemNode):
    """Composite node representing a directory."""

    def isFile(self) -> bool:
        return False

    def listContents(self) -> list:
        return list(self.children.keys())


# ─── Singleton Orchestrator ───────────────────────────────────

class FileSystem:
    """Singleton file system with path-based navigation."""

    _instance = None

    def __new__(cls) -> 'FileSystem':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.root = Directory(name='/')
        return cls._instance

    def isValidPath(self, path: str) -> bool:
        return path is not None and path != "" and path.startswith("/")

    def createPath(self, path: str) -> bool:
        """Create intermediate directories and final node (file or dir) for path."""
        if not self.isValidPath(path):
            return False

        path_components = path.split("/")
        curr = self.root

        for component in path_components[1:-1]:
            if curr.getChild(component) is None:
                new_dir = Directory(component)
                curr.addChild(component, new_dir)
            curr = curr.getChild(component)

        last_component = path_components[-1]
        if last_component == "":
            return False

        if "." in last_component:
            _, ext = last_component.rsplit(".", 1)
            new_node = File(name=last_component, extension=ext, content="")
        else:
            new_node = Directory(last_component)

        curr.addChild(last_component, new_node)
        return True


# ─── Demo ─────────────────────────────────────────────────────

if __name__ == "__main__":
    fs = FileSystem()
    fs.createPath("/home/user/docs")
    fs.createPath("/home/user/docs/notes.txt")

    docs = fs.root.getChild("home").getChild("user").getChild("docs")
    print(f"Contents of /home/user/docs: {docs.listContents()}")

    notes = docs.getChild("notes.txt")
    notes.writeContent("Hello, World!")
    print(f"notes.txt content: {notes.readContent()}")
    
    def getParentPath(self, path: str):
        if path == "/":
            return "/"
        
        pathComponents = path.split("/")
        parent = "/".join(pathComponents[:-1])
        return parent if parent else "/"

    def getNode(self, path: str):
        if path == "/":
            return self.root 
        
        pathComponents = path.split("/")
        curr = self.root
        
        for pathComponent in pathComponents[1:]:
            if curr.getChild(pathComponent) is None:
                return None 
            
            child = curr.getChild(pathComponent)

            curr = child 
        
        return curr

    def deletePath(self, path: str):

        if not self.isValidPath(path):
            return False 
        
        parentPath = self.getParentPath(path)

        parentNode = self.getNode(parentPath)

        childComponent = path.split("/")[-1]

        parentNode.deleteChild(childComponent)
    
    def readFile(self, path: str):
        node = self.getNode(path)
        if node is None or not node.isFile():
            return None 
        return node.readContent()
    
    def writeFile(self, path: str, content: str):
        node = self.getNode(path)
        if node is None or not node.isFile():
            return False 
        node.writeContent(content)
        return True 
    
    def ls(self, path: str):
        node = self.getNode(path)
        if node is None or node.isFile():
            return None 
        return node.listContents()