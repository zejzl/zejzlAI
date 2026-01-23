"""
Community Vault System for ZEJZL.NET
Enables sharing and downloading of tools, configurations, and agent evolutions
"""

import asyncio
import json
import logging
import hashlib
import base64
import sqlite3
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from pathlib import Path
import uuid
import zipfile
import io
import re

logger = logging.getLogger(__name__)

@dataclass
class VaultItem:
    """Represents an item in the community vault"""
    id: str
    name: str
    description: str
    category: str  # 'tool', 'config', 'agent', 'evolution', 'dataset'
    version: str
    author: str
    tags: List[str]
    content: str  # Base64 encoded content or metadata
    content_type: str  # 'json', 'python', 'yaml', 'zip', 'text'
    size_bytes: int
    checksum: str
    dependencies: List[str] = field(default_factory=list)
    compatibility: Dict[str, str] = field(default_factory=dict)  # version requirements
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    downloads: int = 0
    rating: float = 0.0
    rating_count: int = 0
    verified: bool = False
    featured: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VaultItem':
        """Create from dictionary"""
        return cls(**data)

@dataclass
class VaultRating:
    """Represents a user rating for a vault item"""
    item_id: str
    user_id: str
    rating: int  # 1-5 stars
    review: Optional[str] = None
    created_at: float = field(default_factory=time.time)

@dataclass
class VaultDownload:
    """Represents a download record"""
    item_id: str
    user_id: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    downloaded_at: float = field(default_factory=time.time)

class CommunityVault:
    """
    Community vault for sharing ZEJZL.NET tools, configurations, and evolutions
    Supports versioning, ratings, and secure content validation
    """

    def __init__(self, db_path: str = None, content_dir: str = None):
        """
        Initialize community vault

        Args:
            db_path: Path to SQLite database file
            content_dir: Directory for storing vault content
        """
        if db_path is None:
            vault_dir = Path.home() / ".zejzl" / "vault"
            vault_dir.mkdir(parents=True, exist_ok=True)
            db_path = vault_dir / "community_vault.db"

        if content_dir is None:
            content_dir = Path.home() / ".zejzl" / "vault" / "content"

        Path(content_dir).mkdir(parents=True, exist_ok=True)

        self.db_path = Path(db_path)
        self.content_dir = Path(content_dir)

        # Initialize database
        self._init_db()

        # Content validation rules
        self.security_validator = ContentSecurityValidator()

        logger.info(f"Community vault initialized at {db_path}")

    def _init_db(self):
        """Initialize SQLite database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            # Vault items table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS vault_items (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    category TEXT NOT NULL,
                    version TEXT NOT NULL,
                    author TEXT NOT NULL,
                    tags TEXT NOT NULL,  -- JSON array
                    content TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    checksum TEXT NOT NULL,
                    dependencies TEXT,  -- JSON array
                    compatibility TEXT,  -- JSON object
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    downloads INTEGER DEFAULT 0,
                    rating REAL DEFAULT 0.0,
                    rating_count INTEGER DEFAULT 0,
                    verified INTEGER DEFAULT 0,
                    featured INTEGER DEFAULT 0
                )
            """)

            # Ratings table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS vault_ratings (
                    item_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    rating INTEGER NOT NULL,
                    review TEXT,
                    created_at REAL NOT NULL,
                    PRIMARY KEY (item_id, user_id),
                    FOREIGN KEY (item_id) REFERENCES vault_items (id)
                )
            """)

            # Downloads table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS vault_downloads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_id TEXT NOT NULL,
                    user_id TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    downloaded_at REAL NOT NULL,
                    FOREIGN KEY (item_id) REFERENCES vault_items (id)
                )
            """)

            # Categories table for metadata
            conn.execute("""
                CREATE TABLE IF NOT EXISTS vault_categories (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    icon TEXT,
                    sort_order INTEGER DEFAULT 0
                )
            """)

            # Insert default categories
            default_categories = [
                ('tool', 'Tools', 'Custom tools and utilities', 'wrench', 1),
                ('config', 'Configurations', 'System and agent configurations', 'settings', 2),
                ('agent', 'Agents', 'Custom agent implementations', 'bot', 3),
                ('evolution', 'Evolutions', 'Agent evolution patterns', 'zap', 4),
                ('dataset', 'Datasets', 'Training and reference data', 'database', 5),
                ('template', 'Templates', 'Workflow and prompt templates', 'file-text', 6)
            ]

            for cat_id, name, desc, icon, order in default_categories:
                conn.execute("""
                    INSERT OR IGNORE INTO vault_categories
                    (id, name, description, icon, sort_order) VALUES (?, ?, ?, ?, ?)
                """, (cat_id, name, desc, icon, order))

            # Create indexes for better performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_category ON vault_items(category)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_author ON vault_items(author)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON vault_items(created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_rating ON vault_items(rating)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_verified ON vault_items(verified)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_featured ON vault_items(featured)")

            conn.commit()

    async def publish_item(self, item_data: Dict[str, Any], content_bytes: bytes = None,
                          author: str = "anonymous") -> Tuple[bool, str]:
        """
        Publish a new item to the vault

        Args:
            item_data: Item metadata
            content_bytes: Raw content bytes (optional)
            author: Author identifier

        Returns:
            (success, item_id or error_message)
        """
        try:
            # Validate content security
            if content_bytes:
                is_safe, security_issues = await self.security_validator.validate_content(
                    content_bytes, item_data.get('content_type', 'text')
                )
                if not is_safe:
                    return False, f"Security validation failed: {', '.join(security_issues)}"

            # Generate item ID and checksum
            item_id = str(uuid.uuid4())
            content_b64 = ""

            if content_bytes:
                # Store content file
                content_path = self.content_dir / f"{item_id}.content"
                with open(content_path, 'wb') as f:
                    f.write(content_bytes)
                content_b64 = base64.b64encode(content_bytes).decode('utf-8')
            else:
                content_b64 = base64.b64encode(item_data.get('content', '').encode('utf-8')).decode('utf-8')

            checksum = hashlib.sha256(content_b64.encode()).hexdigest()

            # Create vault item
            item = VaultItem(
                id=item_id,
                name=item_data['name'],
                description=item_data['description'],
                category=item_data['category'],
                version=item_data.get('version', '1.0.0'),
                author=author,
                tags=item_data.get('tags', []),
                content=content_b64,
                content_type=item_data.get('content_type', 'json'),
                size_bytes=len(content_b64),
                checksum=checksum,
                dependencies=item_data.get('dependencies', []),
                compatibility=item_data.get('compatibility', {})
            )

            # Store in database
            def _store():
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        INSERT INTO vault_items
                        (id, name, description, category, version, author, tags, content,
                         content_type, size_bytes, checksum, dependencies, compatibility,
                         created_at, updated_at, verified, featured)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        item.id, item.name, item.description, item.category, item.version,
                        item.author, json.dumps(item.tags), item.content, item.content_type,
                        item.size_bytes, item.checksum, json.dumps(item.dependencies),
                        json.dumps(item.compatibility), item.created_at, item.updated_at,
                        1 if item.verified else 0, 1 if item.featured else 0
                    ))
                    conn.commit()

            await asyncio.get_event_loop().run_in_executor(None, _store)

            logger.info(f"Published vault item: {item.name} by {author}")
            return True, item_id

        except Exception as e:
            logger.error(f"Failed to publish vault item: {e}")
            return False, str(e)

    async def get_item(self, item_id: str) -> Optional[VaultItem]:
        """Get a vault item by ID"""
        def _get():
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT * FROM vault_items WHERE id = ?
                """, (item_id,))

                row = cursor.fetchone()
                if not row:
                    return None

                # Convert row to dict
                columns = [desc[0] for desc in cursor.description]
                data = dict(zip(columns, row))

                # Parse JSON fields
                data['tags'] = json.loads(data['tags']) if data['tags'] else []
                data['dependencies'] = json.loads(data['dependencies']) if data['dependencies'] else []
                data['compatibility'] = json.loads(data['compatibility']) if data['compatibility'] else {}

                return VaultItem.from_dict(data)

        return await asyncio.get_event_loop().run_in_executor(None, _get)

    async def download_item(self, item_id: str, user_id: str = None,
                           ip_address: str = None, user_agent: str = None) -> Optional[bytes]:
        """Download a vault item and record the download"""
        item = await self.get_item(item_id)
        if not item:
            return None

        # Record download
        def _record_download():
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO vault_downloads
                    (item_id, user_id, ip_address, user_agent, downloaded_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (item_id, user_id, ip_address, user_agent, time.time()))

                # Update download count
                conn.execute("""
                    UPDATE vault_items SET downloads = downloads + 1 WHERE id = ?
                """, (item_id,))

                conn.commit()

        await asyncio.get_event_loop().run_in_executor(None, _record_download)

        # Return content
        try:
            content_path = self.content_dir / f"{item_id}.content"
            if content_path.exists():
                with open(content_path, 'rb') as f:
                    return f.read()
            else:
                # Return base64 decoded content
                return base64.b64decode(item.content)
        except Exception as e:
            logger.error(f"Failed to read item content {item_id}: {e}")
            return None

    async def search_items(self, query: str = "", category: str = None,
                          author: str = None, tags: List[str] = None,
                          sort_by: str = "downloads", sort_order: str = "desc",
                          limit: int = 50, offset: int = 0) -> List[VaultItem]:
        """Search vault items with filters"""
        def _search():
            with sqlite3.connect(self.db_path) as conn:
                # Build query
                conditions = []
                params = []

                if query:
                    conditions.append("(name LIKE ? OR description LIKE ? OR tags LIKE ?)")
                    query_param = f"%{query}%"
                    params.extend([query_param, query_param, query_param])

                if category:
                    conditions.append("category = ?")
                    params.append(category)

                if author:
                    conditions.append("author = ?")
                    params.append(author)

                if tags:
                    tag_conditions = []
                    for tag in tags:
                        tag_conditions.append("tags LIKE ?")
                        params.append(f"%{tag}%")
                    conditions.append(f"({' OR '.join(tag_conditions)})")

                where_clause = " AND ".join(conditions) if conditions else "1=1"

                # Sort options
                sort_options = {
                    "downloads": "downloads",
                    "rating": "rating",
                    "created_at": "created_at",
                    "updated_at": "updated_at",
                    "name": "name"
                }
                sort_field = sort_options.get(sort_by, "downloads")
                order = "DESC" if sort_order.lower() == "desc" else "ASC"

                cursor = conn.execute(f"""
                    SELECT * FROM vault_items
                    WHERE {where_clause}
                    ORDER BY {sort_field} {order}
                    LIMIT ? OFFSET ?
                """, params + [limit, offset])

                items = []
                columns = [desc[0] for desc in cursor.description]

                for row in cursor:
                    data = dict(zip(columns, row))
                    # Parse JSON fields
                    data['tags'] = json.loads(data['tags']) if data['tags'] else []
                    data['dependencies'] = json.loads(data['dependencies']) if data['dependencies'] else []
                    data['compatibility'] = json.loads(data['compatibility']) if data['compatibility'] else {}
                    items.append(VaultItem.from_dict(data))

                return items

        return await asyncio.get_event_loop().run_in_executor(None, _search)

    async def rate_item(self, item_id: str, user_id: str, rating: int,
                       review: str = None) -> bool:
        """Rate a vault item"""
        if not 1 <= rating <= 5:
            return False

        def _rate():
            with sqlite3.connect(self.db_path) as conn:
                # Insert or update rating
                conn.execute("""
                    INSERT OR REPLACE INTO vault_ratings
                    (item_id, user_id, rating, review, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (item_id, user_id, rating, review, time.time()))

                # Update item rating
                cursor = conn.execute("""
                    SELECT AVG(rating), COUNT(*) FROM vault_ratings WHERE item_id = ?
                """, (item_id,))

                avg_rating, count = cursor.fetchone()
                conn.execute("""
                    UPDATE vault_items SET rating = ?, rating_count = ? WHERE id = ?
                """, (avg_rating or 0, count or 0, item_id))

                conn.commit()
                return True

        try:
            return await asyncio.get_event_loop().run_in_executor(None, _rate)
        except Exception as e:
            logger.error(f"Failed to rate item {item_id}: {e}")
            return False

    async def get_categories(self) -> List[Dict[str, Any]]:
        """Get available vault categories"""
        def _get_categories():
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT * FROM vault_categories ORDER BY sort_order
                """)
                return [dict(zip([desc[0] for desc in cursor.description], row))
                       for row in cursor]

        return await asyncio.get_event_loop().run_in_executor(None, _get_categories)

    async def get_featured_items(self, limit: int = 10) -> List[VaultItem]:
        """Get featured vault items"""
        def _get_featured():
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT * FROM vault_items WHERE featured = 1
                    ORDER BY downloads DESC LIMIT ?
                """, (limit,))

                items = []
                columns = [desc[0] for desc in cursor.description]

                for row in cursor:
                    data = dict(zip(columns, row))
                    data['tags'] = json.loads(data['tags']) if data['tags'] else []
                    data['dependencies'] = json.loads(data['dependencies']) if data['dependencies'] else []
                    data['compatibility'] = json.loads(data['compatibility']) if data['compatibility'] else {}
                    items.append(VaultItem.from_dict(data))

                return items

        return await asyncio.get_event_loop().run_in_executor(None, _get_featured)

    async def get_stats(self) -> Dict[str, Any]:
        """Get vault statistics"""
        def _get_stats():
            with sqlite3.connect(self.db_path) as conn:
                # Item counts by category
                cursor = conn.execute("""
                    SELECT category, COUNT(*) as count
                    FROM vault_items
                    GROUP BY category
                """)
                category_counts = {row[0]: row[1] for row in cursor}

                # Total stats
                cursor = conn.execute("""
                    SELECT COUNT(*), SUM(downloads), AVG(rating)
                    FROM vault_items
                """)
                total_items, total_downloads, avg_rating = cursor.fetchone()

                # Recent activity
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM vault_items
                    WHERE created_at > ?
                """, (time.time() - 86400,))  # Last 24 hours
                recent_items = cursor.fetchone()[0]

                return {
                    "total_items": total_items or 0,
                    "total_downloads": total_downloads or 0,
                    "average_rating": round(avg_rating or 0, 1),
                    "categories": category_counts,
                    "recent_items": recent_items,
                    "featured_items": len(conn.execute("SELECT COUNT(*) FROM vault_items WHERE featured = 1").fetchone())
                }

        return await asyncio.get_event_loop().run_in_executor(None, _get_stats)

class ContentSecurityValidator:
    """Validates content for security issues before vault publication"""

    def __init__(self):
        # Dangerous patterns to check for
        self.dangerous_patterns = [
            r'import\s+os\b',  # OS system access
            r'import\s+subprocess\b',  # Subprocess execution
            r'import\s+sys\b.*exit',  # System exit
            r'eval\s*\(',  # Code evaluation
            r'exec\s*\(',  # Code execution
            r'__import__\s*\(',  # Dynamic imports
            r'open\s*\(.*/etc',  # System file access
            r'open\s*\(.*/proc',  # Process file access
            r'os\.system\s*\(',  # System commands
            r'subprocess\.(call|Popen|run)',  # Subprocess execution
        ]

    async def validate_content(self, content: bytes, content_type: str) -> Tuple[bool, List[str]]:
        """
        Validate content for security issues

        Returns:
            (is_safe, list_of_issues)
        """
        issues = []

        try:
            # Decode content based on type
            if content_type in ['python', 'text']:
                text_content = content.decode('utf-8', errors='ignore')

                # Check for dangerous patterns
                for pattern in self.dangerous_patterns:
                    if re.search(pattern, text_content, re.IGNORECASE):
                        issues.append(f"Dangerous code pattern detected: {pattern}")

                # Check for very long lines (potential obfuscation)
                lines = text_content.split('\n')
                for i, line in enumerate(lines):
                    if len(line) > 1000:
                        issues.append(f"Line {i+1} is unusually long ({len(line)} chars)")

                # Check for base64 encoded content (potential obfuscation)
                base64_pattern = r'[A-Za-z0-9+/]{100,}={0,2}'
                if re.search(base64_pattern, text_content):
                    issues.append("Potential base64 encoded content detected")

            elif content_type == 'json':
                # Try to parse JSON
                try:
                    json.loads(content.decode('utf-8'))
                except json.JSONDecodeError:
                    issues.append("Invalid JSON format")

            elif content_type == 'zip':
                # Check zip file contents
                with zipfile.ZipFile(io.BytesIO(content)) as zf:
                    for file_info in zf.filelist:
                        # Check for executable files
                        if file_info.filename.endswith(('.exe', '.bat', '.cmd', '.sh', '.py')):
                            issues.append(f"Executable file in archive: {file_info.filename}")

                        # Check for system paths
                        if '..' in file_info.filename or file_info.filename.startswith('/'):
                            issues.append(f"Suspicious path in archive: {file_info.filename}")

        except Exception as e:
            issues.append(f"Content validation error: {str(e)}")

        return len(issues) == 0, issues