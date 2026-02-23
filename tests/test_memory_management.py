"""Test memory management features."""

import json
import tempfile
from pathlib import Path

from chatagent.tools.memory import (
    SaveMemoryTool,
    SearchMemoryTool,
    DeleteMemoryTool,
    ClearMemoryTool,
    FilterMemoryByTagTool,
)


def test_memory_management():
    """Test all memory management features."""
    # Create temporary memory file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        memory_file = f.name
        f.write('{"memories": []}')

    try:
        # Initialize tools
        save_tool = SaveMemoryTool(memory_file)
        search_tool = SearchMemoryTool(save_tool)
        delete_tool = DeleteMemoryTool(save_tool)
        clear_tool = ClearMemoryTool(save_tool)
        filter_tool = FilterMemoryByTagTool(save_tool)

        # Test 1: Save memories
        print("Test 1: Saving memories...")
        result = save_tool.execute(
            key="project_name",
            value="ChatAgent",
            tags=["project", "important"]
        )
        assert "Saved memory" in result or "Updated memory" in result
        print(f"✓ {result}")

        result = save_tool.execute(
            key="user_preference",
            value="Use Python 3.11+",
            tags=["preference", "python"]
        )
        assert "Saved memory" in result or "Updated memory" in result
        print(f"✓ {result}")

        result = save_tool.execute(
            key="reminder",
            value="Run tests before committing",
            tags=["reminder"]
        )
        assert "Saved memory" in result or "Updated memory" in result
        print(f"✓ {result}")

        # Test 2: Search memories
        print("\nTest 2: Searching memories...")
        result = search_tool.execute(query="project")
        assert "project_name" in result
        print(f"✓ Found memories matching 'project'")

        # Test 3: Filter by tag
        print("\nTest 3: Filtering by tag...")
        result = filter_tool.execute(tag="python")
        assert "user_preference" in result
        print(f"✓ Found memories with tag 'python'")

        # Test 4: Delete specific memory
        print("\nTest 4: Deleting specific memory...")
        result = delete_tool.execute(key="reminder")
        assert "Successfully deleted" in result
        print(f"✓ {result}")

        # Verify deletion
        memories = save_tool.get_all_memories()
        keys = [m['key'] for m in memories]
        assert "reminder" not in keys
        print("✓ Deletion verified")

        # Test 5: Clear all memories
        print("\nTest 5: Clearing all memories...")
        result = clear_tool.execute()
        assert "Successfully cleared" in result
        print(f"✓ {result}")

        # Verify all cleared
        memories = save_tool.get_all_memories()
        assert len(memories) == 0
        print("✓ All memories cleared")

        print("\n✅ All tests passed!")

    finally:
        # Clean up
        Path(memory_file).unlink(missing_ok=True)


if __name__ == "__main__":
    test_memory_management()
