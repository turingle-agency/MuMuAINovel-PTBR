"""Serviço de memória vetorial - memória de longo prazo e busca semântica (Qdrant via VectorStore)."""
from typing import List, Dict, Any, Optional
import json
from datetime import datetime
from app.logger import get_logger
from app.services.vector import (
    Cond, VectorPoint, get_embedder, get_vector_store,
)
import hashlib

logger = get_logger(__name__)

class MemoryService:
    """向量记忆管理服务 - 实现语义检索和长期记忆"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Não carrega nada: banco vetorial e modelo de embedding são resolvidos sob demanda."""
        self._initialized = True

    @property
    def store(self):
        return get_vector_store()

    @property
    def embedder(self):
        return get_embedder()

    def get_collection(self, user_id: str, project_id: str) -> str:
        """
        获取或创建项目的记忆集合，返回集合名称

        每个用户的每个项目有独立的集合,实现数据隔离。
        名称使用 SHA256 哈希压缩: u_{user_hash}_p_{project_hash}
        """
        collection_name = self._collection_name(user_id, project_id)
        try:
            self.store.ensure_collection(collection_name)
            return collection_name
        except Exception as e:
            logger.error(f"❌ 获取collection失败: {str(e)}")
            raise

    @staticmethod
    def _collection_name(user_id: str, project_id: str) -> str:
        user_hash = hashlib.sha256(user_id.encode()).hexdigest()[:8]
        project_hash = hashlib.sha256(project_id.encode()).hexdigest()[:8]
        return f"u_{user_hash}_p_{project_hash}"

    def _encode(self, text: str) -> List[float]:
        return self.embedder.encode(text).tolist()

    async def add_memory(
        self,
        user_id: str,
        project_id: str,
        memory_id: str,
        content: str,
        memory_type: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """
        添加记忆到向量数据库
        
        Args:
            user_id: 用户ID
            project_id: 项目ID
            memory_id: 记忆唯一ID
            content: 记忆内容(将被转换为向量)
            memory_type: 记忆类型
            metadata: 附加元数据
        
        Returns:
            是否添加成功
        """
        try:
            collection = self.get_collection(user_id, project_id)
            
            # 生成文本的向量表示
            embedding = self._encode(content)
            
            # 准备元数据(值为基础类型)
            payload_meta = {
                "memory_type": memory_type,
                "chapter_id": str(metadata.get("chapter_id", "")),
                "chapter_number": int(metadata.get("chapter_number", 0)),
                "importance": float(metadata.get("importance_score", 0.5)),
                "tags": json.dumps(metadata.get("tags", []), ensure_ascii=False),
                "title": str(metadata.get("title", ""))[:200],  # 限制长度
                "is_foreshadow": int(metadata.get("is_foreshadow", 0)),
                "created_at": datetime.now().isoformat()
            }
            
            # 添加相关角色信息
            if metadata.get("related_characters"):
                payload_meta["related_characters"] = json.dumps(
                    metadata["related_characters"], 
                    ensure_ascii=False
                )
            
            # 存储到向量库
            self.store.upsert(collection, [VectorPoint(
                id=memory_id, document=content, payload=payload_meta, vector=embedding
            )])
            
            logger.info(f"✅ 记忆已添加: {memory_id[:8]}... (类型:{memory_type}, 重要性:{payload_meta['importance']})")
            return True
            
        except Exception as e:
            logger.error(f"❌ 添加记忆失败: {str(e)}")
            return False
    
    async def batch_add_memories(
        self,
        user_id: str,
        project_id: str,
        memories: List[Dict[str, Any]]
    ) -> int:
        """
        批量添加记忆(性能更好)
        
        Args:
            user_id: 用户ID
            project_id: 项目ID
            memories: 记忆列表,每个包含id、content、type、metadata
        
        Returns:
            成功添加的数量
        """
        if not memories:
            return 0
            
        try:
            collection = self.get_collection(user_id, project_id)
            
            points = []
            embeddings = self.embedder.encode([m['content'] for m in memories]).tolist()
            
            # 批量准备数据
            for mem, embedding in zip(memories, embeddings):
                # 准备元数据
                metadata = mem.get('metadata', {})
                payload_meta = {
                    "memory_type": mem['type'],
                    "chapter_id": str(metadata.get("chapter_id", "")),
                    "chapter_number": int(metadata.get("chapter_number", 0)),
                    "importance": float(metadata.get("importance_score", 0.5)),
                    "tags": json.dumps(metadata.get("tags", []), ensure_ascii=False),
                    "title": str(metadata.get("title", ""))[:200],
                    "is_foreshadow": int(metadata.get("is_foreshadow", 0)),
                    "created_at": datetime.now().isoformat()
                }
                points.append(VectorPoint(
                    id=mem['id'], document=mem['content'], payload=payload_meta, vector=embedding
                ))
            
            # 批量添加
            self.store.upsert(collection, points)
            
            logger.info(f"✅ 批量添加记忆成功: {len(memories)}条")
            return len(memories)
            
        except Exception as e:
            logger.error(f"❌ 批量添加记忆失败: {str(e)}")
            return 0
    
    async def search_memories(
        self,
        user_id: str,
        project_id: str,
        query: str,
        memory_types: Optional[List[str]] = None,
        limit: int = 10,
        min_importance: float = 0.0,
        chapter_range: Optional[tuple] = None
    ) -> List[Dict[str, Any]]:
        """
        语义搜索相关记忆
        
        Args:
            user_id: 用户ID
            project_id: 项目ID
            query: 查询文本(会被转换为向量进行相似度搜索)
            memory_types: 过滤特定类型的记忆
            limit: 返回结果数量
            min_importance: 最低重要性阈值
            chapter_range: 章节范围 (start, end)
        
        Returns:
            相关记忆列表,按相似度排序
        """
        try:
            collection = self.get_collection(user_id, project_id)
            
            query_embedding = self._encode(query)
            
            conditions: List[Cond] = []
            if memory_types:
                conditions.append(Cond("memory_type", "in", list(memory_types)))
            if min_importance > 0:
                conditions.append(Cond("importance", "gte", min_importance))
            if chapter_range:
                conditions.append(Cond("chapter_number", "gte", chapter_range[0]))
                conditions.append(Cond("chapter_number", "lte", chapter_range[1]))
            
            hits = self.store.query(collection, query_embedding, limit, conditions or None)
            
            memories = [
                {
                    "id": hit.id,
                    "content": hit.document,
                    "metadata": hit.payload,
                    "similarity": hit.score,
                    "distance": 1 - hit.score,
                }
                for hit in hits
            ]
            
            logger.info(f"🔍 语义搜索完成: 查询='{query[:30]}...', 找到{len(memories)}条记忆")
            return memories
            
        except Exception as e:
            logger.error(f"❌ 搜索记忆失败: {str(e)}")
            return []
    
    async def get_recent_memories(
        self,
        user_id: str,
        project_id: str,
        current_chapter: int,
        recent_count: int = 3,
        min_importance: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        获取最近几章的重要记忆(用于保持连贯性)
        
        Args:
            user_id: 用户ID
            project_id: 项目ID
            current_chapter: 当前章节号
            recent_count: 获取最近几章
            min_importance: 最低重要性阈值
        
        Returns:
            最近章节的记忆列表,按重要性排序
        """
        try:
            collection = self.get_collection(user_id, project_id)
            
            # 计算章节范围
            start_chapter = max(1, current_chapter - recent_count)
            
            # 获取最近章节的记忆
            points = self.store.get(collection, [
                Cond("chapter_number", "gte", start_chapter),
                Cond("chapter_number", "lte", current_chapter - 1),
                Cond("importance", "gte", min_importance),
            ])[:100]  # 先获取足够多的记忆
            
            memories = [
                {"id": p.id, "content": p.document, "metadata": p.payload}
                for p in points
            ]
            
            # 按重要性和章节号排序
            memories.sort(
                key=lambda x: (float(x['metadata'].get('importance', 0)), 
                              int(x['metadata'].get('chapter_number', 0))),
                reverse=True
            )
            
            # 返回最重要的前N条
            top_memories = memories[:20]
            logger.info(f"📚 获取最近记忆: 章节{start_chapter}-{current_chapter-1}, 找到{len(top_memories)}条")
            return top_memories
            
        except Exception as e:
            logger.error(f"❌ 获取最近记忆失败: {str(e)}")
            return []
    
    async def find_unresolved_foreshadows(
        self,
        user_id: str,
        project_id: str,
        current_chapter: int
    ) -> List[Dict[str, Any]]:
        """
        查找未完结的伏笔
        
        Args:
            user_id: 用户ID
            project_id: 项目ID
            current_chapter: 当前章节号
        
        Returns:
            未完结伏笔列表
        """
        try:
            collection = self.get_collection(user_id, project_id)
            
            # 查找伏笔状态为1(已埋下但未回收)的记忆
            points = self.store.get(collection, [
                Cond("is_foreshadow", "eq", 1),
                Cond("chapter_number", "lte", current_chapter - 1),
            ])[:50]
            
            foreshadows = [
                {"id": p.id, "content": p.document, "metadata": p.payload}
                for p in points
            ]
            
            # 按重要性排序
            foreshadows.sort(
                key=lambda x: float(x['metadata'].get('importance', 0)),
                reverse=True
            )
            
            logger.info(f"🎣 找到未完结伏笔: {len(foreshadows)}个")
            return foreshadows
            
        except Exception as e:
            logger.error(f"❌ 查找伏笔失败: {str(e)}")
            return []
    
    async def build_context_for_generation(
        self,
        user_id: str,
        project_id: str,
        current_chapter: int,
        chapter_outline: str,
        character_names: List[str] = None
    ) -> Dict[str, Any]:
        """
        为章节生成构建智能上下文
        
        这是核心功能: 结合多种检索策略,为AI生成提供最相关的记忆
        
        Args:
            user_id: 用户ID
            project_id: 项目ID
            current_chapter: 当前章节号
            chapter_outline: 本章大纲
            character_names: 涉及的角色名列表
        
        Returns:
            包含各种上下文信息的字典
        """
        logger.info(f"🧠 开始构建章节{current_chapter}的智能上下文...")
        
        # 1. 获取最近章节上下文(时间连续性)
        recent = await self.get_recent_memories(
            user_id, project_id, current_chapter, 
            recent_count=3, min_importance=0.5
        )
        
        # 2. 语义搜索相关记忆
        relevant = await self.search_memories(
            user_id=user_id,
            project_id=project_id,
            query=chapter_outline,
            limit=10,
            min_importance=0.4
        )
        
        # 3. 查找未完结伏笔
        foreshadows = await self.find_unresolved_foreshadows(
            user_id, project_id, current_chapter
        )
        
        # 4. 如果有指定角色,获取角色相关记忆
        character_memories = []
        if character_names:
            character_query = " ".join(character_names) + " 角色 状态 关系"
            character_memories = await self.search_memories(
                user_id=user_id,
                project_id=project_id,
                query=character_query,
                memory_types=["character_event", "plot_point"],
                limit=8
            )
        
        # 5. 获取重要情节点
        # 注意：ChromaDB的where条件需要特殊处理，不能同时使用多个顶层条件
        try:
            plot_points = await self.search_memories(
                user_id=user_id,
                project_id=project_id,
                query="重要 转折 高潮 关键",
                memory_types=["plot_point", "hook"],
                limit=5,
                min_importance=0.7
            )
        except Exception as e:
            logger.error(f"❌ 搜索记忆失败: {str(e)}")
            # 降级处理：分别查询
            plot_points = []
            try:
                plot_points = await self.search_memories(
                    user_id=user_id,
                    project_id=project_id,
                    query="重要 转折 高潮 关键",
                    memory_types=["plot_point", "hook"],
                    limit=5
                )
            except Exception as e2:
                logger.warning(f"⚠️ 降级查询也失败: {str(e2)}")
                plot_points = []
        
        context = {
            "recent_context": self._format_memories(recent, "最近章节记忆"),
            "relevant_memories": self._format_memories(relevant, "语义相关记忆"),
            "character_states": self._format_memories(character_memories, "角色相关记忆"),
            "foreshadows": self._format_memories(foreshadows[:5], "未完结伏笔"),
            "plot_points": self._format_memories(plot_points, "重要情节点"),
            "stats": {
                "recent_count": len(recent),
                "relevant_count": len(relevant),
                "character_count": len(character_memories),
                "foreshadow_count": len(foreshadows),
                "plot_point_count": len(plot_points)
            }
        }
        
        logger.info(f"✅ 上下文构建完成: 最近{len(recent)}条, 相关{len(relevant)}条, 伏笔{len(foreshadows)}个")
        return context
    def _format_memories(self, memories: List[Dict], section_title: str = "记忆") -> str:
        """
        格式化记忆列表为文本
        
        Args:
            memories: 记忆列表
            section_title: 章节标题
        
        Returns:
            格式化后的文本
        """
        if not memories:
            return f"【{section_title}】\n暂无相关记忆\n"
        
        lines = [f"【{section_title}】"]
        for i, mem in enumerate(memories, 1):
            meta = mem.get('metadata', {})
            chapter_num = meta.get('chapter_number', '?')
            mem_type = meta.get('memory_type', '未知')
            importance = float(meta.get('importance', 0.5))
            title = meta.get('title', '')
            content = mem['content']
            
            # 格式: [序号] 第X章-类型(重要性) 标题: 内容
            line = f"{i}. [第{chapter_num}章-{mem_type}★{importance:.1f}]"
            if title:
                line += f" {title}: {content[:100]}"
            else:
                line += f" {content[:150]}"
            lines.append(line)
        
        return "\n".join(lines) + "\n"
    
    async def delete_foreshadow_memories(
        self,
        user_id: str,
        project_id: str,
        foreshadow_keywords: List[str]
    ) -> int:
        """
        根据伏笔关键词删除向量库中的相关伏笔记忆
        
        说明：当前记忆系统未持久化 [reference_foreshadow_id](backend/app/services/prompt_service.py:1109) /
        [foreshadow_id](backend/app/services/foreshadow_service.py:230) 映射，因此这里采用内容关键词匹配作为清理策略，
        仅删除 [memory_type='foreshadow'](backend/app/models/memory.py:23) 的向量记忆。
        
        Args:
            user_id: 用户ID
            project_id: 项目ID
            foreshadow_keywords: 伏笔关键词列表
        
        Returns:
            实际删除数量
        """
        try:
            keywords = [kw.strip() for kw in foreshadow_keywords if kw and kw.strip()]
            if not keywords:
                return 0

            collection = self.get_collection(user_id, project_id)
            points = self.store.get(collection, [Cond("memory_type", "eq", "foreshadow")])

            ids_to_delete = []
            for point in points:
                title = str((point.payload or {}).get('title', ''))
                haystack = f"{title}\n{point.document}".lower()

                if any(keyword.lower() in haystack for keyword in keywords):
                    ids_to_delete.append(point.id)

            if ids_to_delete:
                self.store.delete(collection, ids=ids_to_delete)
                logger.info(f"🗑️ 已删除项目{project_id[:8]}的{len(ids_to_delete)}条伏笔相关向量记忆")

            return len(ids_to_delete)

        except Exception as e:
            logger.error(f"❌ 删除伏笔相关向量记忆失败: {str(e)}")
            return 0

    async def delete_chapter_memories(
        self,
        user_id: str,
        project_id: str,
        chapter_id: str
    ) -> bool:
        """
        删除指定章节的所有记忆
        
        Args:
            user_id: 用户ID
            project_id: 项目ID
            chapter_id: 章节ID
        
        Returns:
            是否删除成功
        """
        try:
            collection = self.get_collection(user_id, project_id)
            
            where = [Cond("chapter_id", "eq", chapter_id)]
            removed = self.store.count(collection, where)
            if removed:
                self.store.delete(collection, where=where)
                logger.info(f"🗑️ 已删除章节{chapter_id[:8]}的{removed}条记忆")
            else:
                logger.info(f"ℹ️ 章节{chapter_id[:8]}没有记忆需要删除")
            return True
                
        except Exception as e:
            logger.error(f"❌ 删除章节记忆失败: {str(e)}")
            return False
    
    async def delete_project_memories(
        self,
        user_id: str,
        project_id: str
    ) -> bool:
        """
        删除指定项目的所有记忆(包括向量数据库)
        
        Args:
            user_id: 用户ID
            project_id: 项目ID
        
        Returns:
            是否删除成功
        """
        try:
            collection_name = self._collection_name(user_id, project_id)
            
            # 删除整个collection(不存在也算成功)
            self.store.delete_collection(collection_name)
            logger.info(f"🗑️ 已删除项目{project_id[:8]}的向量数据库collection: {collection_name}")
            return True
                
        except Exception as e:
            logger.error(f"❌ 删除项目记忆失败: {str(e)}")
            return False
    
    async def update_memory(
        self,
        user_id: str,
        project_id: str,
        memory_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        更新记忆内容或元数据
        
        Args:
            user_id: 用户ID
            project_id: 项目ID
            memory_id: 记忆ID
            content: 新内容(可选)
            metadata: 新元数据(可选)
        
        Returns:
            是否更新成功
        """
        try:
            collection = self.get_collection(user_id, project_id)
            
            new_payload: Dict[str, Any] = {}
            if metadata:
                for key, value in metadata.items():
                    if isinstance(value, (list, dict)):
                        new_payload[key] = json.dumps(value, ensure_ascii=False)
                    else:
                        new_payload[key] = value
            
            if content:
                # 内容变化: 重新生成embedding并整体重写该点(保留旧元数据)
                existing = self.store.get(collection, [Cond("_id", "eq", memory_id)])
                if not existing:
                    logger.warning(f"⚠️ 记忆不存在: {memory_id[:8]}...")
                    return False
                payload = {**existing[0].payload, **new_payload}
                self.store.upsert(collection, [VectorPoint(
                    id=memory_id, document=content, payload=payload, vector=self._encode(content)
                )])
            elif new_payload:
                self.store.set_payload(collection, memory_id, new_payload)
            else:
                logger.warning("⚠️ 没有提供更新内容")
                return False
            
            logger.info(f"✅ 记忆已更新: {memory_id[:8]}...")
            return True
                
        except Exception as e:
            logger.error(f"❌ 更新记忆失败: {str(e)}")
            return False
    
    async def get_memory_stats(
        self,
        user_id: str,
        project_id: str
    ) -> Dict[str, Any]:
        """
        获取记忆统计信息
        
        Args:
            user_id: 用户ID
            project_id: 项目ID
        
        Returns:
            统计信息字典
        """
        try:
            collection = self.get_collection(user_id, project_id)
            
            # 获取所有记忆
            all_points = self.store.get(collection)
            
            if not all_points:
                return {
                    "total_count": 0,
                    "by_type": {},
                    "by_chapter": {},
                    "foreshadow_count": 0
                }
            
            metadatas = [p.payload for p in all_points]
            
            # 统计各类型数量
            type_counts = {}
            chapter_counts = {}
            foreshadow_count = 0
            
            for meta in metadatas:
                mem_type = meta.get('memory_type', 'unknown')
                chapter_num = meta.get('chapter_number', 0)
                is_foreshadow = meta.get('is_foreshadow', 0)
                
                type_counts[mem_type] = type_counts.get(mem_type, 0) + 1
                chapter_counts[str(chapter_num)] = chapter_counts.get(str(chapter_num), 0) + 1
                
                if is_foreshadow == 1:
                    foreshadow_count += 1
            
            stats = {
                "total_count": len(all_points),
                "by_type": type_counts,
                "by_chapter": chapter_counts,
                "foreshadow_count": foreshadow_count,
                "foreshadow_resolved": sum(1 for m in metadatas if m.get('is_foreshadow') == 2)
            }
            
            logger.info(f"📊 记忆统计: 总计{stats['total_count']}条, 伏笔{foreshadow_count}个")
            return stats
            
        except Exception as e:
            logger.error(f"❌ 获取统计信息失败: {str(e)}")
            return {"error": str(e)}


# 创建全局实例
memory_service = MemoryService()
