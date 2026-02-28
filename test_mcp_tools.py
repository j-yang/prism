#!/usr/bin/env python3
"""Test PRISM MCP Server tools without starting the server."""

import sys

sys.path.insert(0, "src")

from prism.mcp.server import (
    list_deliverables,
    lookup_als_field,
    get_bronze_schema,
    get_meta_variables,
)


def test_list_deliverables():
    """Test list_deliverables tool."""
    mock_path = "examples/some_study/AZ-GC012F-IIM & SSC_1st_data sharing tlf shell_v0.5_20260211_draft.docx"

    print("=" * 60)
    print("Testing: list_deliverables")
    print("=" * 60)

    try:
        result = list_deliverables(mock_path)
        print(result[:500])  # 只显示前500字符
        print("\n✅ list_deliverables 工作正常")
        return True
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


def test_lookup_als():
    """Test lookup_als_field tool."""
    als_path = "examples/some_study/D8318N00001_ALS.xlsx"

    print("\n" + "=" * 60)
    print("Testing: lookup_als_field")
    print("=" * 60)

    try:
        result = lookup_als_field(als_path, domain="DM", keywords="age")
        print(result[:500])  # 只显示前500字符
        print("\n✅ lookup_als_field 工作正常")
        return True
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


def main():
    """Run all tests."""
    print("\n🧪 PRISM MCP Server 工具测试\n")

    results = []
    results.append(test_list_deliverables())
    results.append(test_lookup_als())

    print("\n" + "=" * 60)
    print("测试结果")
    print("=" * 60)
    print(f"通过: {sum(results)}/{len(results)}")

    if all(results):
        print("\n✅ 所有测试通过！PRISM MCP Server已就绪。")
        return 0
    else:
        print("\n⚠️ 部分测试失败，请检查错误信息。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
