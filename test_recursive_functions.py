#!/usr/bin/env python3
"""
Test suite for recursive budget analysis functions.
Demonstrates recursion concepts in the context of budget planning.
"""

import sys
sys.path.append('.')

from main import (
    TimelineItem, BudgetTimeline, BudgetNode,
    create_hierarchical_budget_tree,
    recursive_budget_optimization,
    recursive_timeline_search
)
from datetime import datetime, timedelta
import json

def create_sample_timeline() -> BudgetTimeline:
    """Create a comprehensive sample timeline for testing recursive functions."""
    
    # Create diverse timeline items across different categories and locations
    items = [
        # Transportation - Multiple locations and dates
        TimelineItem(
            id="flight_1", title="Flight LAX to NYC", description="Round-trip flight",
            date="2025-01-15", time="08:00", cost=450.0, category="✈️ Transportation",
            location="Los Angeles to New York", duration_hours=6.0, ai_suggested=True
        ),
        TimelineItem(
            id="flight_2", title="Flight NYC to Paris", description="International flight",
            date="2025-01-20", time="10:00", cost=650.0, category="✈️ Transportation", 
            location="New York to Paris", duration_hours=8.0, ai_suggested=True
        ),
        TimelineItem(
            id="taxi_1", title="Airport Taxi", description="Taxi to hotel",
            date="2025-01-20", time="18:00", cost=45.0, category="✈️ Transportation",
            location="Paris", duration_hours=0.5, ai_suggested=False
        ),
        
        # Food & Dining - Different locations and price ranges
        TimelineItem(
            id="dinner_1", title="Fine Dining Restaurant", description="Michelin star restaurant",
            date="2025-01-15", time="19:00", cost=120.0, category="🍽️ Food & Dining",
            location="New York", duration_hours=2.5, ai_suggested=True
        ),
        TimelineItem(
            id="lunch_1", title="Cafe Lunch", description="Local Parisian cafe",
            date="2025-01-21", time="12:00", cost=35.0, category="🍽️ Food & Dining",
            location="Paris", duration_hours=1.0, ai_suggested=True
        ),
        TimelineItem(
            id="dinner_2", title="Street Food Tour", description="Local food experience",
            date="2025-01-21", time="18:00", cost=65.0, category="🍽️ Food & Dining",
            location="Paris", duration_hours=3.0, ai_suggested=False
        ),
        
        # Accommodation - Multiple cities
        TimelineItem(
            id="hotel_1", title="NYC Hotel", description="3-night stay in Manhattan",
            date="2025-01-15", time="15:00", cost=450.0, category="🏨 Accommodation",
            location="New York", duration_hours=72.0, ai_suggested=True
        ),
        TimelineItem(
            id="hotel_2", title="Paris Boutique Hotel", description="4-night stay near Louvre",
            date="2025-01-20", time="16:00", cost=680.0, category="🏨 Accommodation",
            location="Paris", duration_hours=96.0, ai_suggested=True
        ),
        
        # Entertainment & Activities - Mixed locations
        TimelineItem(
            id="show_1", title="Broadway Show", description="Hamilton tickets",
            date="2025-01-16", time="20:00", cost=150.0, category="🎭 Entertainment",
            location="New York", duration_hours=3.0, ai_suggested=False
        ),
        TimelineItem(
            id="museum_1", title="Metropolitan Museum", description="Museum visit",
            date="2025-01-17", time="10:00", cost=30.0, category="🎨 Culture",
            location="New York", duration_hours=4.0, ai_suggested=True
        ),
        TimelineItem(
            id="museum_2", title="Louvre Museum", description="World-famous art museum",
            date="2025-01-22", time="09:00", cost=20.0, category="🎨 Culture",
            location="Paris", duration_hours=5.0, ai_suggested=True
        ),
        TimelineItem(
            id="tour_1", title="Seine River Cruise", description="Romantic evening cruise",
            date="2025-01-22", time="19:00", cost=85.0, category="🎯 Activities",
            location="Paris", duration_hours=2.0, ai_suggested=False
        ),
        
        # Shopping
        TimelineItem(
            id="shopping_1", title="Souvenir Shopping", description="Local crafts and gifts",
            date="2025-01-23", time="14:00", cost=150.0, category="🛍️ Shopping",
            location="Paris", duration_hours=2.0, ai_suggested=False
        )
    ]
    
    return BudgetTimeline(
        items=items,
        total_budget=3000.0,
        currency="USD",
        start_date="2025-01-15",
        end_date="2025-01-25",
        location="Multi-city Trip"
    )

def test_hierarchical_budget_tree():
    """Test the hierarchical budget tree creation function."""
    print("🌳 Testing Hierarchical Budget Tree Creation")
    print("=" * 60)
    
    timeline = create_sample_timeline()
    
    # Custom budget rules for testing
    budget_rules = {
        "🍽️ Food & Dining": {"percentage": 0.20, "priority": 2},
        "✈️ Transportation": {"percentage": 0.35, "priority": 1},
        "🏨 Accommodation": {"percentage": 0.30, "priority": 1},
        "🎭 Entertainment": {"percentage": 0.08, "priority": 3},
        "🛍️ Shopping": {"percentage": 0.05, "priority": 4},
        "🎨 Culture": {"percentage": 0.02, "priority": 3}
    }
    
    # Create the hierarchical tree
    budget_tree = create_hierarchical_budget_tree(timeline, budget_rules)
    
    def print_tree_recursive(node: BudgetNode, level: int = 0):
        """Recursively print the budget tree structure."""
        indent = "  " * level
        utilization = f"{node.utilization_rate:.1f}%"
        
        print(f"{indent}📁 {node.name}")
        print(f"{indent}   💰 Budget: ${node.allocated_budget:.2f} | Spent: ${node.actual_cost:.2f}")
        print(f"{indent}   📊 Utilization: {utilization} | Items: {len(node.items)}")
        
        # Base case for printing: don't go too deep
        if level < 3 and node.children:
            for child in node.children:
                print_tree_recursive(child, level + 1)
    
    print_tree_recursive(budget_tree)
    
    # Calculate and display tree statistics
    def calculate_stats_recursive(node: BudgetNode) -> dict:
        """Recursively calculate tree statistics."""
        if not node.children:
            return {
                "nodes": 1, 
                "leaves": 1, 
                "max_depth": 0,
                "categories": {node.category} if node.category else set()
            }
        
        stats = {"nodes": 1, "leaves": 0, "max_depth": 0, "categories": set()}
        if node.category:
            stats["categories"].add(node.category)
        
        for child in node.children:
            child_stats = calculate_stats_recursive(child)
            stats["nodes"] += child_stats["nodes"]
            stats["leaves"] += child_stats["leaves"]
            stats["max_depth"] = max(stats["max_depth"], child_stats["max_depth"] + 1)
            stats["categories"].update(child_stats["categories"])
        
        return stats
    
    stats = calculate_stats_recursive(budget_tree)
    
    print(f"\n📈 Tree Statistics:")
    print(f"   Total Nodes: {stats['nodes']}")
    print(f"   Leaf Nodes: {stats['leaves']}")
    print(f"   Maximum Depth: {stats['max_depth']}")
    print(f"   Unique Categories: {len(stats['categories'])}")
    
    print("\n✅ Hierarchical Budget Tree Test Completed!\n")
    return budget_tree

def test_recursive_optimization(budget_tree: BudgetNode):
    """Test the recursive budget optimization function."""
    print("⚡ Testing Recursive Budget Optimization")
    print("=" * 60)
    
    optimization_results = recursive_budget_optimization(budget_tree, optimization_factor=0.12)
    
    def print_optimization_recursive(results: dict, level: int = 0):
        """Recursively print optimization results."""
        indent = "  " * level
        
        print(f"{indent}🎯 {results['node_name']} (Depth: {results['depth']})")
        print(f"{indent}   💰 Budget: ${results['allocated_budget']:.2f} | Actual: ${results['current_cost']:.2f}")
        print(f"{indent}   📊 Utilization: {results['utilization_rate']:.1f}%")
        
        # Print suggestions
        if results.get('suggestions'):
            print(f"{indent}   💡 Suggestions ({len(results['suggestions'])}):")
            for suggestion in results['suggestions']:
                severity_symbol = {"high": "🔥", "medium": "⚠️", "low": "💡"}
                symbol = severity_symbol.get(suggestion['severity'], "💡")
                print(f"{indent}     {symbol} {suggestion['message']}")
        
        # Recursive case: print children
        if results.get('children_analyses'):
            for child_results in results['children_analyses']:
                print_optimization_recursive(child_results, level + 1)
    
    print_optimization_recursive(optimization_results)
    
    # Count total suggestions recursively
    def count_suggestions_recursive(results: dict) -> int:
        """Recursively count total suggestions across all levels."""
        count = len(results.get('suggestions', []))
        
        if results.get('children_analyses'):
            for child_results in results['children_analyses']:
                count += count_suggestions_recursive(child_results)
        
        return count
    
    total_suggestions = count_suggestions_recursive(optimization_results)
    print(f"\n📊 Generated {total_suggestions} total optimization suggestions")
    print("✅ Recursive Optimization Test Completed!\n")

def test_recursive_timeline_search():
    """Test the recursive timeline search function."""
    print("🔍 Testing Recursive Timeline Search")
    print("=" * 60)
    
    timeline = create_sample_timeline()
    
    # Test Case 1: Simple search
    print("Test Case 1: Simple category search")
    criteria1 = {"category": "Food"}
    results1 = recursive_timeline_search(timeline.items, criteria1)
    print(f"   Found {len(results1)} food-related items")
    for item in results1:
        print(f"   - {item.title} (${item.cost:.2f})")
    
    # Test Case 2: Range-based search
    print("\nTest Case 2: Cost range search")
    criteria2 = {"cost_range": (100, 500)}
    results2 = recursive_timeline_search(timeline.items, criteria2)
    print(f"   Found {len(results2)} items in $100-$500 range")
    for item in results2:
        print(f"   - {item.title}: ${item.cost:.2f}")
    
    # Test Case 3: Nested search with AND logic
    print("\nTest Case 3: Nested AND search")
    criteria3 = {
        "location": "Paris",
        "and": {
            "cost_range": (0, 100)
        }
    }
    results3 = recursive_timeline_search(timeline.items, criteria3)
    print(f"   Found {len(results3)} items in Paris under $100")
    for item in results3:
        print(f"   - {item.title} in {item.location}: ${item.cost:.2f}")
    
    # Test Case 4: Complex nested search
    print("\nTest Case 4: Complex nested search")
    criteria4 = {
        "category": "Culture",
        "or": {
            "location": "New York",
            "and": {
                "cost_range": (15, 50)
            }
        }
    }
    results4 = recursive_timeline_search(timeline.items, criteria4)
    print(f"   Found {len(results4)} cultural items matching complex criteria")
    for item in results4:
        print(f"   - {item.title} in {item.location}: ${item.cost:.2f}")
    
    print("✅ Recursive Timeline Search Test Completed!\n")

def test_recursion_edge_cases():
    """Test edge cases and base conditions for recursive functions."""
    print("🧪 Testing Recursion Edge Cases")
    print("=" * 60)
    
    # Test with empty timeline
    print("Test 1: Empty timeline")
    empty_timeline = BudgetTimeline([], 1000.0, "USD", "2025-01-01", "2025-01-01", "Test")
    empty_tree = create_hierarchical_budget_tree(empty_timeline)
    print(f"   Empty tree children: {len(empty_tree.children)}")
    print(f"   Empty tree cost: ${empty_tree.actual_cost:.2f}")
    
    # Test with single item
    print("\nTest 2: Single item timeline")
    single_item = TimelineItem(
        id="test_1", title="Test Item", description="Single item test",
        date="2025-01-01", time="12:00", cost=50.0, category="🎯 Activities",
        location="Test Location", duration_hours=1.0
    )
    single_timeline = BudgetTimeline([single_item], 100.0, "USD", "2025-01-01", "2025-01-01", "Test")
    single_tree = create_hierarchical_budget_tree(single_timeline)
    print(f"   Single item tree children: {len(single_tree.children)}")
    print(f"   Single item tree has category children: {len(single_tree.children[0].children) if single_tree.children else 0}")
    
    # Test search with no matches
    print("\nTest 3: Search with no matches")
    no_match_criteria = {"category": "NonexistentCategory"}
    no_results = recursive_timeline_search([single_item], no_match_criteria)
    print(f"   No match search results: {len(no_results)}")
    
    # Test optimization with balanced budget
    print("\nTest 4: Optimization with balanced budget")
    if single_tree.children:
        balanced_optimization = recursive_budget_optimization(single_tree.children[0], 0.1)
        suggestion_count = len(balanced_optimization.get('suggestions', []))
        print(f"   Balanced budget suggestions: {suggestion_count}")
    
    print("✅ Edge Cases Test Completed!\n")

def demonstrate_recursion_concepts():
    """Demonstrate key recursion concepts used in the budget functions."""
    print("📚 Demonstrating Recursion Concepts")
    print("=" * 60)
    
    print("""
    The recursive functions in this budget planner demonstrate several key concepts:
    
    1. 📁 BASE CASES (Stopping Conditions):
       - Empty item lists (no more data to process)
       - Maximum recursion depth (prevent infinite loops)
       - Single items (no need to subdivide further)
    
    2. 🔄 RECURSIVE CASES (Self-Referential Calls):
       - Budget tree creation calls itself with subcategories
       - Optimization analysis processes children recursively
       - Search applies nested criteria through recursive calls
    
    3. 📊 STATE REDUCTION:
       - Each recursive call works with smaller datasets
       - Depth parameter increases to track progress
       - Filters narrow down search space progressively
    
    4. 🧮 RESULT AGGREGATION:
       - Tree statistics combine results from all branches
       - Optimization suggestions merge from all levels
       - Search results union or intersect based on logic
    
    5. 🛡️ DEPTH LIMITING:
       - Maximum depth prevents stack overflow
       - Base cases ensure termination
       - Graceful handling of edge cases
    """)
    
    print("✅ Recursion Concepts Demonstration Complete!\n")

def run_comprehensive_tests():
    """Run all recursive function tests in sequence."""
    print("🚀 Starting Comprehensive Recursive Functions Test Suite")
    print("=" * 80)
    
    try:
        # Test hierarchical budget tree creation
        budget_tree = test_hierarchical_budget_tree()
        
        # Test recursive optimization
        test_recursive_optimization(budget_tree)
        
        # Test recursive timeline search
        test_recursive_timeline_search()
        
        # Test edge cases
        test_recursion_edge_cases()
        
        # Demonstrate concepts
        demonstrate_recursion_concepts()
        
        print("🎉 All Tests Passed Successfully!")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("✨ Recursive Budget Analysis Functions - Test Suite")
    print("This test suite demonstrates recursion in budget planning context.\n")
    
    success = run_comprehensive_tests()
    
    if success:
        print("\n💡 Key Takeaways:")
        print("   - Recursion breaks complex problems into smaller, manageable pieces")
        print("   - Base cases prevent infinite loops and provide termination conditions")
        print("   - Recursive algorithms can elegantly handle hierarchical data structures")
        print("   - Budget planning benefits from recursive analysis and optimization")
        print("   - Real-world applications make recursion concepts more understandable")
    else:
        print("\n⚠️ Some tests failed. Please check the error messages above.")