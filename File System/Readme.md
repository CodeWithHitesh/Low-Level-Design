# File System — Low Level Design

## Problem Statement (as asked in interviews)

> Design an in-memory File System that supports creating files and directories, navigating paths, reading/writing file content, and listing directory contents. The system should model a hierarchical tree structure similar to Unix-like file systems.

---

## Candidate Understanding (first 2–3 minutes)

- The file system is a **tree** — directories can contain files and other directories.
- Every entry (file or directory) has a **name**, **path**, and metadata (created time, size).
- The system supports **absolute paths** like `/home/user/docs/resume.txt`.
- Files hold **content** (text); directories hold **children** (files and sub-directories).
- There is a single **root directory** (`/`) as the entry point.

---

## Scope for a 45-minute Round

### Core Features (implement)

| # | Feature | Key Classes / Pattern |
|---|---------|----------------------|
| 1 | File and directory modeling with shared interface | `FileSystemNode` (ABC), `File`, `Directory` — **Composite Pattern** |
| 2 | Create file/directory at a given path (mkdir -p) | `FileSystem.createPath()` |
| 3 | Navigate/resolve a path to the correct node | `FileSystem.getNode()` |
| 4 | Read content of a file by path | `FileSystem.readFile()` → `File.readContent()` |
| 5 | Write content to a file by path | `FileSystem.writeFile()` → `File.writeContent()` |
| 6 | List contents of a directory (ls) | `FileSystem.ls()` → `Directory.listContents()` |
| 7 | Delete a file or directory | `FileSystem.deletePath()` |
| 8 | Single file system instance | `FileSystem` — **Singleton Pattern** |

### TODO Features (out of scope — mention to interviewer but don't code)

- **TODO:** Move / rename a file or directory
- **TODO:** Copy a file or directory (deep copy for directories)
- **TODO:** Search / find files by name or pattern (glob/regex)
- **TODO:** Permissions model (read/write/execute per user/group)
- **TODO:** Symbolic links and hard links
- **TODO:** File system size limits / quota enforcement
- **TODO:** Undo/redo operations (Memento pattern)
- **TODO:** Observer notifications on file changes (watchers)
- **TODO:** Thread-safety for concurrent read/write access

---

## Design Patterns Used

| Pattern | Where | Why |
|---------|-------|-----|
| **Composite** | `FileSystemNode` (ABC) → `File` (leaf) / `Directory` (composite) | Treat files and directories uniformly — both are tree nodes with the same interface (`getChild`, `addChild`, `isFile`). Enables recursive traversal without type checks. |
| **Singleton** | `FileSystem.__new__()` | Ensures a single file system instance throughout the application, matching the real-world constraint of one root file system. |

### Composite Pattern — How it works here

The Composite pattern has **3 roles**:

```
Component  (FileSystemNode)  ──  common interface for all nodes
    ├── Leaf       (File)    ──  end node, holds content, no meaningful children
    └── Composite  (Directory) ── contains children (both Files and Directories)
```

**Why it fits:** A file system is a tree. When traversing a path like `/home/user/docs`, each call to `getChild()` works the same regardless of whether the current node is a deeply nested directory or a simple one. The client code (`FileSystem.getNode`, `createPath`) never does `isinstance` checks — it just calls the shared interface methods (`getChild`, `addChild`, `isFile`). This is the core benefit of Composite: **uniform treatment of leaves and composites**.

**Real-world analogy:** The Unix VFS (Virtual File System) layer treats everything as an inode — files, directories, devices — all implement the same operations. Our `FileSystemNode` ABC is the simplified version of that.

---

## Class Overview

```
FileSystemNode (ABC)  ◄── File (leaf) / Directory (composite)
    │  - name, lastModified, createdAt, children
    │  - addChild(name, child)
    │  - getChild(name) → FileSystemNode | None
    │  - deleteChild(name)
    │  - isFile()  [abstract]
    │
File
    │  - content, extension
    │  - readContent() → str
    │  - writeContent(content)
    │
Directory
    │  - listContents() → List[str]
    │
FileSystem (Singleton)
    │  - root: Directory
    │  - createPath(path)
    │  - getNode(path) → FileSystemNode | None
    │  - deletePath(path)
    │  - readFile(path) → str | None
    │  - writeFile(path, content) → bool
    │  - ls(path) → List[str]
```

---

## How to Walk Through in the Interview

1. **Clarify** scope (2 min) — confirm in-memory only, absolute paths, no permissions, no symlinks.
2. **Identify** classes top-down (3 min) — FileSystemNode → File / Directory → FileSystem.
3. **Code** core classes in order (35 min):
   - FileSystemNode (ABC with Composite interface) → File (leaf) → Directory (composite) → FileSystem (Singleton + CRUD operations)
4. **Mention** TODO features verbally (2 min) — move/rename, permissions, watchers, copy, search.
5. **Dry-run** a path end-to-end (3 min) — e.g. `createPath("/home/user/resume.txt")` → traverses root → creates `home` dir → creates `user` dir → creates `resume.txt` file.

---

## Extensibility (Verbal Discussion Points)

- **Iterator pattern** — for recursive tree traversal (e.g., `find` command searching all nested directories)
- **Observer pattern** — for file watchers that get notified on create/modify/delete events
- **Strategy pattern** — for pluggable search algorithms (name match, glob, regex)
- **Memento pattern** — for undo/redo of file operations (move, delete, rename)
