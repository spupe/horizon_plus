"""Daily summary generation — pure programmatic rendering."""

import re
from typing import List, Dict

from ..models import ContentItem


_CJK = r"[\u4e00-\u9fff\u3400-\u4dbf]"
_ASCII = r"[A-Za-z0-9]"


def _pangu(text: str) -> str:
    """Insert a space between CJK and ASCII letters/digits (Pangu spacing)."""
    text = re.sub(rf"({_CJK})({_ASCII})", r"\1 \2", text)
    text = re.sub(rf"({_ASCII})({_CJK})", r"\1 \2", text)
    return text


LABELS = {
    "en": {
        "header": "Horizon Daily",
        "source": "Source",
        "background": "Background",
        "discussion": "Discussion",
        "references": "References",
        "tags": "Tags",
        "multi_source": "Multi-Source Coverage",
        "synthesis": "Cross-Source Synthesis",
        "perspectives": "Source Perspectives",
        "empty_body": (
            "No significant developments today. This might indicate:\n"
            "- A quiet day in your tracked sources\n"
            "- The AI score threshold is too high\n"
            "- Your information sources need expansion\n\n"
            "Consider:\n"
            "1. Lowering the `ai_score_threshold` in config.json\n"
            "2. Adding more diverse information sources\n"
            "3. Checking if the AI model is working correctly\n"
        ),
    },
    "zh": {
        "header": "Horizon 每日速递",
        "source": "来源",
        "background": "背景",
        "discussion": "社区讨论",
        "references": "参考链接",
        "tags": "标签",
        "multi_source": "多源报道",
        "synthesis": "跨源综合分析",
        "perspectives": "各来源视角",
        "empty_body": (
            "今日暂无重要动态，可能原因：\n"
            "- 今天关注的信息源较平静\n"
            "- AI 评分阈值设置过高\n"
            "- 信息源种类有待扩充\n\n"
            "建议：\n"
            "1. 在 config.json 中降低 `ai_score_threshold`\n"
            "2. 添加更多多样化的信息源\n"
            "3. 检查 AI 模型是否正常工作\n"
        ),
    },
}


class DailySummarizer:
    """Generates daily Markdown summaries from pre-analyzed content items."""

    def __init__(self):
        pass

    async def generate_summary(
        self,
        items: List[ContentItem],
        date: str,
        total_fetched: int,
        language: str = "en",
    ) -> str:
        """Generate daily summary in Markdown format.

        Items are rendered in score-descending order (already sorted by orchestrator).

        Args:
            items: High-scoring content items (already enriched)
            date: Date string (YYYY-MM-DD)
            total_fetched: Total number of items fetched before filtering
            language: Output language, either "en" or "zh"

        Returns:
            str: Markdown formatted summary
        """
        labels = LABELS.get(language, LABELS["en"])

        if not items:
            return self._generate_empty_summary(date, total_fetched, labels)

        header = (
            f"# {labels['header']} - {date}\n\n"
            f"> From {total_fetched} items, {len(items)} important content pieces were selected\n\n"
            "---\n\n"
        )

        # TOC
        toc_entries = []
        for i, item in enumerate(items):
            _t = item.metadata.get(f"title_{language}") or item.title
            t = str(_t).replace("[", "(").replace("]", ")")
            if language == "zh":
                t = _pangu(t)
            score = item.ai_score or "?"
            toc_entries.append(f"{i + 1}. [{t}](#item-{i + 1}) \u2b50\ufe0f {score}/10")
        toc = "\n".join(toc_entries) + "\n\n---\n\n"

        parts = [self._format_item(item, labels, language, i + 1) for i, item in enumerate(items)]

        return header + toc + "".join(parts)

    def _format_item(self, item: ContentItem, labels: dict, language: str, index: int) -> str:
        """Format a single ContentItem into Markdown."""
        meta = item.metadata
        is_multi = meta.get("is_multi_source", False)

        # Use unified title for multi-source items if available
        if is_multi and meta.get(f"unified_title_{language}"):
            _title = meta[f"unified_title_{language}"]
        else:
            _title = meta.get(f"title_{language}") or item.title
        title = str(_title).replace("[", "(").replace("]", ")")
        url = str(item.url)
        score = item.ai_score or "?"

        summary = (
            meta.get(f"detailed_summary_{language}")
            or meta.get("detailed_summary")
            or item.ai_summary
            or ""
        )

        if language == "zh":
            title = _pangu(title)
            summary = _pangu(summary)

        # Source line
        source_type = item.source_type.value
        if is_multi:
            perspectives = meta.get("source_perspectives", [])
            source_names = [p["source"] for p in perspectives]
            source_line = " \u00b7 ".join(source_names)
        else:
            source_parts = [source_type]
            if meta.get("subreddit"):
                source_parts.append(f"r/{meta['subreddit']}")
            if meta.get("feed_name"):
                source_parts.append(meta["feed_name"])
            else:
                source_parts.append(item.author or "unknown")
            if item.published_at:
                day = item.published_at.strftime("%d").lstrip("0")
                source_parts.append(item.published_at.strftime(f"%b {day}, %H:%M"))
            source_line = " \u00b7 ".join(source_parts)

        # Multi-source badge in header
        header_suffix = ""
        if is_multi:
            header_suffix = f" \U0001f4f0 {labels['multi_source']}"

        lines = [
            f'<a id="item-{index}"></a>',
            f"## [{title}]({url}) \u2b50\ufe0f {score}/10{header_suffix}",
            "",
            summary,
            "",
            source_line,
        ]

        # Cross-source synthesis for multi-source items
        if is_multi:
            synthesis = meta.get(f"synthesis_{language}") or ""
            if language == "zh" and synthesis:
                synthesis = _pangu(synthesis)
            if synthesis:
                lines.append("")
                lines.append(f"**{labels['synthesis']}**: {synthesis}")

            # Per-source angles
            source_angles = meta.get("source_angles", [])
            if source_angles:
                lines.append("")
                lines.append(f"**{labels['perspectives']}**:")
                for angle in source_angles:
                    angle_text = angle.get(f"angle_{language}") or angle.get("angle_en", "")
                    if language == "zh" and angle_text:
                        angle_text = _pangu(angle_text)
                    if angle_text:
                        lines.append(f"- **{angle.get('source', '?')}**: {angle_text}")

            # Links to all source URLs
            perspectives = meta.get("source_perspectives", [])
            if len(perspectives) > 1:
                lines.append("")
                for p in perspectives:
                    p_title = p.get("title", p["source"])
                    lines.append(f"- [{p['source']}: {p_title}]({p['url']})")

        # Source attribution block
        source_links = []

        # Primary article URL (already in the title link, but repeat for clarity)
        source_links.append(f"- [{item.title[:80]}]({url})")

        # Discussion thread URLs (HN, Reddit)
        discussion_url = meta.get("discussion_url")
        if discussion_url and discussion_url != str(item.url):
            source_label = source_type
            if source_type == "hackernews":
                source_label = "Hacker News discussion"
            elif source_type == "reddit":
                source_label = f"Reddit discussion (r/{meta.get('subreddit', '')})"
            source_links.append(f"- [{source_label}]({discussion_url})")

        # Multi-source: show all source URLs
        if is_multi:
            perspectives = meta.get("source_perspectives", [])
            for p in perspectives:
                p_url = p.get("url", "")
                if p_url and p_url != str(item.url):
                    disc = p.get("discussion_url", "")
                    p_label = p.get("source", p.get("source_type", ""))
                    if disc and disc != p_url:
                        source_links.append(f"- [{p_label} discussion]({disc})")
                    else:
                        p_title = p.get("title", p_label)[:80]
                        source_links.append(f"- [{p_label}: {p_title}]({p_url})")

        # Web search references
        web_sources = meta.get("sources") or []
        for s in web_sources:
            source_links.append(f"- [{s['title']}]({s['url']})")

        if source_links:
            lines.append("")
            lines.append(f"**{labels['source']}s**:")
            lines.extend(source_links)

        if item.ai_tags:
            tags_str = ", ".join([f"`#{t}`" for t in item.ai_tags])
            lines.append("")
            lines.append(f"**{labels['tags']}**: {tags_str}")

        lines.append("")
        lines.append("---")

        return "\n".join(lines) + "\n\n"

    def _generate_empty_summary(self, date: str, total_fetched: int, labels: dict) -> str:
        """Generate summary when no high-scoring items were found."""
        return (
            f"# {labels['header']} - {date}\n\n"
            f"> Analyzed {total_fetched} items, but none met the importance threshold.\n\n"
            + labels["empty_body"]
        )
