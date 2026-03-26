from dataclasses import dataclass, field
from datetime import date, datetime
from typing import List, Dict
from abc import abstractmethod, ABC


@dataclass
class FileSystemNode(ABC):
    name: str 
    lastModified: date = field(default_factory=datetime.now)
    createdAt: date = field(default_factory=datetime.now)
    children: Dict[str, 'FileSystemNode'] = field(default_factory=dict)

    @abstractmethod
    def isFile(self):
        pass 

    def addChild(self, name, child: 'FileSystemNode'):
        self.children[name] = child
        self.lastModified = datetime.now()
    
    def getChild(self, name):
        return self.children.get(name, None)

    def deleteChild(self, name):
        if name not in self.children:
            print("Child does not exists!")
            return 
        self.children.pop(name)
    

@dataclass
class File(FileSystemNode):
    content: str = field(default_factory=str)
    extension: str = field(default_factory=str)

    def isFile(self):
        return True 
    
    def readContent(self):
        return self.content
    
    def writeContent(self, content):
        self.content = content
        self.lastModified = datetime.now()
    

@dataclass
class Directory(FileSystemNode):
    
    def isFile(self):
        return False 
    
    def listContents(self):
        return list(self.children.keys())


class FileSystem:
    
    _instance = None 

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.root = Directory(name='/')
        return cls._instance

    def isValidPath(self, path: str):

        return path is not None and path != "" and path.startswith("/")

    def createPath(self, path: str):
        if not self.isValidPath(path):
            return False 
        
        pathComponents = path.split("/")
        curr = self.root
        
        for pathComponent in pathComponents[1:-1]:
            if curr.getChild(pathComponent) is None:
                newDir = Directory(pathComponent)
                curr.addChild(pathComponent, newDir)
            
            child = curr.getChild(pathComponent)

            curr = child 
        
        lastPathComponent = pathComponents[-1]
        if lastPathComponent == "":
            return False 

        newNode = None 
        if "." in lastPathComponent:
            _, ext = lastPathComponent.rsplit(".", 1)
            newNode = File(name=lastPathComponent, extension=ext, content="")
        else:
            newNode = Directory(lastPathComponent)

        curr.addChild(lastPathComponent, newNode)
        return True 
    
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