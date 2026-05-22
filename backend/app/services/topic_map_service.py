"""
Topic Map Service.

Handles topic node hierarchy, cycle prevention, and gap analysis rules.
"""

import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.topic_node import TopicNode
from app.models.content_item import ContentItem
from app.models.project import Project
from app.core.exceptions import BadRequestException, NotFoundException


class TopicMapService:
    """Service for Topic Map hierarchy management."""

    async def get_node(self, db: AsyncSession, node_id: uuid.UUID) -> Optional[TopicNode]:
        """Get a topic node by ID."""
        result = await db.execute(
            select(TopicNode)
            .where(TopicNode.id == node_id)
            .options(selectinload(TopicNode.children))
        )
        return result.scalars().first()

    async def list_by_project(self, db: AsyncSession, project_id: uuid.UUID) -> List[TopicNode]:
        """List all topic nodes in a project."""
        result = await db.execute(
            select(TopicNode)
            .where(TopicNode.project_id == project_id)
            .order_by(TopicNode.sort_order.asc(), TopicNode.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_tree(self, db: AsyncSession, project_id: uuid.UUID) -> List[Dict[str, Any]]:
        """Get topic nodes structured as a hierarchical tree."""
        nodes = await self.list_by_project(db, project_id)
        
        # Build node map
        node_map = {}
        for node in nodes:
            node_map[node.id] = {
                "id": node.id,
                "project_id": node.project_id,
                "parent_id": node.parent_id,
                "name": node.name,
                "topic_role": node.topic_role,
                "description": node.description,
                "journey_stage": node.journey_stage,
                "priority": node.priority,
                "supports": node.supports or [],
                "supported_by": node.supported_by or [],
                "status": node.status,
                "sort_order": node.sort_order,
                "created_at": node.created_at,
                "updated_at": node.updated_at,
                "children": []
            }
            
        tree = []
        for n_id, tree_node in node_map.items():
            parent_id = tree_node["parent_id"]
            if parent_id and parent_id in node_map:
                node_map[parent_id]["children"].append(tree_node)
            else:
                tree.append(tree_node)
                
        return tree

    async def create_node(
        self, db: AsyncSession, project_id: uuid.UUID, node_data: Dict[str, Any]
    ) -> TopicNode:
        """Create a new topic node."""
        parent_id = node_data.get("parent_id")
        if parent_id:
            parent = await self.get_node(db, parent_id)
            if not parent:
                raise NotFoundException(f"Parent node {parent_id} not found.")
            if parent.project_id != project_id:
                raise BadRequestException("Parent node must belong to the same project.")
                
        node = TopicNode(project_id=project_id, **node_data)
        db.add(node)
        await db.commit()
        await db.refresh(node)
        return node

    async def update_node(
        self, db: AsyncSession, node_id: uuid.UUID, node_data: Dict[str, Any]
    ) -> TopicNode:
        """Update fields of a topic node."""
        node = await self.get_node(db, node_id)
        if not node:
            raise NotFoundException("Topic node not found.")
            
        for key, val in node_data.items():
            if hasattr(node, key):
                setattr(node, key, val)
                
        await db.commit()
        await db.refresh(node)
        return node

    async def move_node(
        self, db: AsyncSession, node_id: uuid.UUID, new_parent_id: Optional[uuid.UUID]
    ) -> TopicNode:
        """Move a node under a new parent, performing cycle prevention checks."""
        node = await self.get_node(db, node_id)
        if not node:
            raise NotFoundException("Topic node not found.")
            
        if new_parent_id:
            # 1. Cannot move under itself
            if node_id == new_parent_id:
                raise BadRequestException("Cannot move a node under itself.")
                
            # 2. Target parent must exist and belong to the same project
            parent = await self.get_node(db, new_parent_id)
            if not parent:
                raise NotFoundException("Target parent node not found.")
            if parent.project_id != node.project_id:
                raise BadRequestException("Target parent must belong to the same project.")
                
            # 3. Cycle prevention: Target parent cannot be a descendant of node
            # Fetch all descendants recursively
            descendants = await self._get_all_descendant_ids(db, node_id)
            if new_parent_id in descendants:
                raise BadRequestException("Cannot move a node under one of its own sub-nodes (creates cycle).")

        node.parent_id = new_parent_id
        await db.commit()
        await db.refresh(node)
        return node

    async def _get_all_descendant_ids(self, db: AsyncSession, node_id: uuid.UUID) -> List[uuid.UUID]:
        """Helper to get all recursive child IDs of a node."""
        all_nodes = await db.execute(select(TopicNode).where(TopicNode.parent_id.isnot(None)))
        nodes_list = list(all_nodes.scalars().all())
        
        # Build parent-to-children mapping
        parent_map = {}
        for n in nodes_list:
            parent_map.setdefault(n.parent_id, []).append(n.id)
            
        # Standard BFS/DFS to accumulate descendant IDs
        descendants = []
        stack = [node_id]
        while stack:
            current = stack.pop()
            children = parent_map.get(current, [])
            for child in children:
                descendants.append(child)
                stack.append(child)
                
        return descendants

    async def list_gaps(self, db: AsyncSession, project_id: uuid.UUID) -> List[Dict[str, Any]]:
        """Identify topic gaps and warnings in the project's planning map."""
        # Fetch project details to check mode
        project_res = await db.execute(select(Project).where(Project.id == project_id))
        project = project_res.scalars().first()
        if not project:
            raise NotFoundException("Project not found.")

        gaps = []
        nodes = await self.list_by_project(db, project_id)
        
        # Build children quick count
        node_children = {}
        for node in nodes:
            if node.parent_id:
                node_children[node.parent_id] = node_children.get(node.parent_id, 0) + 1

        # Gap 1: Pillar node with no supporting/comparison/decision children
        for node in nodes:
            if node.topic_role == "pillar" and node.status != "archived":
                children_count = node_children.get(node.id, 0)
                if children_count == 0:
                    gaps.append({
                        "type": "empty_pillar",
                        "severity": "medium",
                        "node_id": node.id,
                        "title": f"空核心主題: {node.name}",
                        "description": f"主核心主題『{node.name}』下方尚未規劃任何子主題（支持、FAQ、評測等）。請利用評估控制台新增關聯主題節點。"
                    })

        # Gap 2: Existing site mode has unmapped content library items
        if project.mode == "existing_site":
            unmapped_res = await db.execute(
                select(ContentItem)
                .where(ContentItem.project_id == project_id)
                .where(ContentItem.mapped_topic_id.is_(None))
            )
            unmapped_items = list(unmapped_res.scalars().all())
            if unmapped_items:
                gaps.append({
                    "type": "unmapped_content",
                    "severity": "low",
                    "title": f"未分類文章庫 ({len(unmapped_items)} 篇)",
                    "description": f"內容庫中有 {len(unmapped_items)} 篇從舊站匯入的文章尚未對應到任何主題節點。請至主題地圖工作區進行映射分類。"
                })

        return gaps


topic_map_service = TopicMapService()
