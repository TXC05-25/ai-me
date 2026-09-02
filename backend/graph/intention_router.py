"""
意图路由工具 Schema
===================
5 类意图：
  - profile_qa       个人信息问答（教育/背景/性格等）
  - project_detail   项目细节（具体技术实现/难点/方案）
  - skill_assessment 技能评估（掌握程度/原理/对比）
  - small_talk       闲聊寒暄
  - meta_question    关于本项目本身的问题（架构/部署/选型）
"""

from __future__ import annotations

from langchain_core.tools import tool


INTENTION_ROUTER_TOOL = tool(
    "classify_intent",  # 第一位置参数：name_or_callable
    description=(
        "分析用户问题并输出结构化路由信息。"
        "返回字段：thinking（思考过程）、intent（意图分类）、routed_query（用于检索的优化问题）。"
    ),
    args_schema={
        "type": "object",
        "properties": {
            "thinking": {
                "type": "string",
                "description": "思考过程，≤200 字。分析用户意图、识别潜在考察点。",
            },
            "intent": {
                "type": "string",
                "enum": [
                    "profile_qa",
                    "project_detail",
                    "skill_assessment",
                    "small_talk",
                    "meta_question",
                ],
                "description": "意图分类",
            },
            "routed_query": {
                "type": "string",
                "description": "用于检索的优化问句（去除口语化），≤80 字",
            },
        },
        "required": ["thinking", "intent", "routed_query"],
    },
)