# -*- coding: utf-8 -*-
"""
归档写入模块
============

实施计划关联：docs/调研/05-回复归档与存储.md

功能：
- 将待发布的回复写入 pending/ 目录
- 管理归档目录结构
- pending/ → archive/ 文件流转

使用方式：
    archiver = Archiver(archive_dir="archive/", pending_dir="pending/")
    archiver.process_approved_pending_files()
"""
from __future__ import annotations

import logging
import shutil
from pathlib import Path

import frontmatter

logger = logging.getLogger(__name__)


class Archiver:
    """回复归档器

    管理 pending/ → archive/ 的文件流转。
    人工审核通过后，将 pending 文件移动到对应文章的归档目录。

    Args:
        archive_dir: 归档根目录路径
        pending_dir: 待审核目录路径
    """

    def __init__(self, archive_dir: str, pending_dir: str):
        self.archive_dir = Path(archive_dir)
        self.pending_dir = Path(pending_dir)

    def process_approved_pending_files(self):
        """处理所有已审核通过的 pending 文件

        检查 pending/ 下 status=approved 的文件，
        移动到 archive/articles/{article_id}/replies/
        """
        if not self.pending_dir.exists():
            return

        for md_file in self.pending_dir.glob("*.md"):
            try:
                post = frontmatter.load(str(md_file))
                if post.metadata.get("status") == "approved":
                    self._archive_file(md_file, post.metadata)
            except Exception as e:
                logger.warning(f"处理 pending 文件失败 {md_file.name}: {e}")

    def _archive_file(self, file_path: Path, metadata: dict):
        """归档单个文件

        Args:
            file_path: pending 文件路径
            metadata: front-matter 元数据
        """
        article_id = metadata.get("article_id", "unknown")
        dest_dir = (
            self.archive_dir / "articles" / article_id / "replies"
        )
        dest_dir.mkdir(parents=True, exist_ok=True)

        dest_path = dest_dir / file_path.name
        shutil.move(str(file_path), str(dest_path))
        logger.info(f"已归档: {file_path.name} → {dest_path}")
