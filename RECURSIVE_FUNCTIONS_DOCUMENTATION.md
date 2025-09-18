# Recursive Functions in AI Budget Timeline Planner

## 📋 Overview

This document explains the implementation and usage of recursive functions in the AI Budget Timeline Planner. These functions demonstrate practical applications of recursion in budget planning, hierarchical data analysis, and optimization algorithms.

## 🔄 Implemented Recursive Functions

### 1. Hierarchical Budget Tree Creation

#### `create_hierarchical_budget_tree(timeline, budget_rules)`

**Purpose**: Recursively creates a multi-level budget breakdown tree from timeline items.

**Recursion Strategy**:
- **Base Case**: Empty timeline or no items to process
- **Recursive Case**: Creates subcategories by calling helper functions that subdivide data further

```python
def create_hierarchical_budget_tree(timeline: BudgetTimeline, budget_rules: Dict[str, Dict] = None) -> BudgetNode:
    # Base case: Empty timeline
    if not timeline.items:
        return empty_root_node
    
    # Recursive case: Create category subcategories
    for category, items in category_items.items():
        category_node.children = create_budget_subcategories(items, allocated_budget, category)
        # ↑ This calls another recursive function
```

**Key Features**:
- Groups budget items by category, location, and date hierarchically
- Calculates proportional budget allocation at each level
- Creates tree structure with parent-child relationships
- Handles multiple levels of nesting automatically

#### `create_budget_subcategories(items, parent_budget, parent_category)`

**Purpose**: Recursively subdivides budget categories into location and date-based subcategories.

**Recursion Strategy**:
- **Base Case**: Fewer than 2 items (no need to subdivide)
- **Recursive Case 1**: Multiple locations → create location subcategories
- **Recursive Case 2**: Single location → subdivide by date

```python
def create_budget_subcategories(items: List[TimelineItem], parent_budget: float, parent_category: str):
    # Base case: Not enough items to subdivide
    if len(items) <= 1:
        return []
    
    # Recursive case: Create location-based subcategories
    if len(locations) > 1:
        for location, location_items in locations.items():
            location_node.children = create_date_subcategories(location_items, allocated_budget, location_node.category)
            # ↑ Another recursive call
```

### 2. Recursive Budget Optimization

#### `recursive_budget_optimization(node, optimization_factor, depth)`

**Purpose**: Recursively analyzes budget allocation and suggests optimizations across the hierarchy.

**Recursion Strategy**:
- **Base Case**: Maximum depth reached or no children to analyze
- **Recursive Case**: Analyzes each child node and aggregates results

```python
def recursive_budget_optimization(node: BudgetNode, optimization_factor: float = 0.1, depth: int = 0):
    # Base case: Max depth or leaf node
    if depth > 5 or not node.children:
        return analysis_results
    
    # Recursive case: Analyze children
    for child in node.children:
        child_analysis = recursive_budget_optimization(child, optimization_factor, depth + 1)
        # ↑ Recursive call with incremented depth
        child_analyses.append(child_analysis)
```

**Optimization Features**:
- Identifies over-budget categories (>120% utilization)
- Detects under-utilized budget allocations (<50% usage)
- Suggests reallocation opportunities between sibling categories
- Provides severity-based recommendations (high/medium/low)
- Tracks analysis depth to prevent infinite recursion

### 3. Recursive Timeline Search

#### `recursive_timeline_search(timeline_items, search_criteria, depth)`

**Purpose**: Recursively searches timeline items with nested AND/OR criteria.

**Recursion Strategy**:
- **Base Case**: No items, maximum depth, or no nested criteria
- **Recursive Case**: Applies nested criteria with logical operators

```python
def recursive_timeline_search(timeline_items: List[TimelineItem], search_criteria: Dict[str, Any], depth: int = 0):
    # Base case: No items or max depth
    if not timeline_items or depth > 3:
        return timeline_items
    
    # Recursive case: Apply nested criteria
    for nested_key, nested_value in nested_criteria.items():
        if nested_key == "and":
            recursive_results = recursive_timeline_search(filtered_items, nested_value, depth + 1)
            # ↑ Recursive AND operation
```

**Search Capabilities**:
- Supports nested AND/OR logic
- Filters by category, location, cost range, duration range, date range
- Handles complex nested criteria structures
- Prevents infinite recursion with depth limiting
- Returns intersection (AND) or union (OR) of results

## 🧮 Recursion Concepts Demonstrated

### 1. Base Cases (Termination Conditions)

All recursive functions include clear base cases to prevent infinite recursion:

```python
# Empty data base case
if not items or len(items) <= 1:
    return []

# Depth limiting base case  
if depth > maximum_depth:
    return current_results

# No children base case
if not node.children:
    return leaf_analysis
```

### 2. State Reduction

Each recursive call works with smaller or simpler data:

```python
# Subdividing item lists
location_items = [item for item in items if item.location == target_location]
recursive_call(location_items, ...)  # Smaller dataset

# Incrementing depth
recursive_call(..., depth + 1)  # Progress toward base case

# Filtering criteria
filtered_items = apply_current_filters(items)
recursive_call(filtered_items, ...)  # Reduced search space
```

### 3. Result Aggregation

Recursive calls combine results from multiple branches:

```python
# Tree statistics aggregation
total_nodes = 1  # Current node
for child in node.children:
    child_stats = calculate_stats_recursive(child)
    total_nodes += child_stats["total_nodes"]  # Combine results

# Optimization suggestions aggregation
all_suggestions = current_suggestions.copy()
for child_analysis in children_analyses:
    all_suggestions.extend(child_analysis["suggestions"])
```

### 4. Depth Control

All functions implement depth tracking to prevent stack overflow:

```python
def recursive_function(..., depth: int = 0):
    MAX_DEPTH = 5
    if depth > MAX_DEPTH:
        return base_case_result
    
    return recursive_function(..., depth + 1)
```

## 🎯 Real-World Applications

### Budget Planning Applications

1. **Hierarchical Budget Breakdown**
   - Multi-level organizational budgets
   - Project cost breakdown structures
   - Department/team budget allocation

2. **Optimization Analysis**
   - Iterative budget improvement
   - Resource reallocation strategies
   - Performance variance analysis

3. **Advanced Search and Filtering**
   - Complex criteria-based reporting
   - Nested business rule evaluation
   - Multi-dimensional data analysis

### Educational Value

The recursive functions demonstrate:

- **Problem Decomposition**: Breaking complex problems into smaller, manageable pieces
- **Divide and Conquer**: Solving large problems by solving smaller subproblems
- **Tree Traversal**: Navigating hierarchical data structures efficiently
- **Dynamic Programming**: Optimizing overlapping subproblems
- **Backtracking**: Exploring solution spaces systematically

## 🚀 Usage Examples

### Creating a Budget Tree

```python
# Create timeline with budget items
timeline = BudgetTimeline(items=budget_items, total_budget=3000.0, ...)

# Define custom budget allocation rules
budget_rules = {
    "🍽️ Food & Dining": {"percentage": 0.25, "priority": 2},
    "✈️ Transportation": {"percentage": 0.30, "priority": 1},
    "🏨 Accommodation": {"percentage": 0.35, "priority": 1}
}

# Generate hierarchical budget tree
budget_tree = create_hierarchical_budget_tree(timeline, budget_rules)

# Access tree structure
print(f"Root budget: ${budget_tree.allocated_budget:.2f}")
print(f"Categories: {len(budget_tree.children)}")
for child in budget_tree.children:
    print(f"  {child.name}: {child.utilization_rate:.1f}% utilized")
```

### Running Optimization Analysis

```python
# Perform recursive optimization
optimization_results = recursive_budget_optimization(
    budget_tree, 
    optimization_factor=0.15  # 15% reallocation factor
)

# Access optimization suggestions
total_suggestions = optimization_results["total_suggestions"]
print(f"Generated {total_suggestions} optimization suggestions")

# Process suggestions by severity
for suggestion in optimization_results["suggestions"]:
    if suggestion["severity"] == "high":
        print(f"🔥 URGENT: {suggestion['message']}")
```

### Advanced Timeline Search

```python
# Define complex search criteria
search_criteria = {
    "category": "Food",
    "location": "Paris",
    "cost_range": (20, 100),
    "and": {
        "duration_range": (1.0, 3.0),
        "or": {
            "date_range": ("2025-01-20", "2025-01-25")
        }
    }
}

# Execute recursive search
matching_items = recursive_timeline_search(timeline.items, search_criteria)

print(f"Found {len(matching_items)} items matching complex criteria:")
for item in matching_items:
    print(f"  - {item.title}: ${item.cost:.2f} in {item.location}")
```

## 🔧 Technical Implementation Details

### Performance Characteristics

- **Time Complexity**: O(n log n) for tree creation, O(n) for optimization analysis
- **Space Complexity**: O(h) where h is tree height (typically O(log n))
- **Recursion Depth**: Limited to 5 levels to prevent stack overflow
- **Memory Usage**: Efficient due to shared data references in tree nodes

### Error Handling

```python
try:
    budget_tree = create_hierarchical_budget_tree(timeline)
except RecursionError:
    # Handle maximum recursion depth exceeded
    logger.error("Budget tree too complex, using simplified structure")
    budget_tree = create_simple_tree(timeline)
except ValueError as e:
    # Handle invalid input data
    logger.error(f"Invalid timeline data: {e}")
    return None
```

### Integration with Streamlit UI

The recursive functions integrate seamlessly with the Streamlit interface:

```python
# UI Button to generate budget tree
if st.button("🌲 Generate Budget Tree"):
    with st.spinner("Building hierarchical budget tree..."):
        st.session_state.budget_tree = create_hierarchical_budget_tree(st.session_state.timeline)
    st.success("Budget tree generated!")

# Recursive UI rendering
def render_budget_node(node: BudgetNode, level: int = 0):
    if level > 3:  # Base case for UI depth
        return
    
    # Render current node
    st.markdown(f"{'  ' * level}📁 {node.name}")
    
    # Recursive case: render children
    for child in node.children:
        render_budget_node(child, level + 1)
```

## 📚 Learning Outcomes

After studying these recursive implementations, you should understand:

1. **Recursive Problem Solving**
   - Identifying recursive substructures in real-world problems
   - Designing effective base cases and recursive cases
   - Managing recursion depth and preventing infinite loops

2. **Data Structure Design**
   - Creating hierarchical data models
   - Tree traversal algorithms
   - Parent-child relationship management

3. **Algorithm Optimization**
   - Analyzing time and space complexity of recursive algorithms
   - Implementing tail recursion where applicable
   - Balancing recursion depth vs. performance

4. **Practical Applications**
   - Financial analysis and budget optimization
   - Search algorithms with complex criteria
   - Hierarchical data processing in business contexts

## 🎓 Extended Learning

To further explore recursion concepts:

1. **Implement additional recursive features**:
   - Budget forecasting with recursive projections
   - Timeline conflict detection using recursive checking
   - Multi-currency conversion with recursive rate calculations

2. **Study related algorithms**:
   - Dynamic programming for budget optimization
   - Backtracking for constraint satisfaction
   - Divide-and-conquer for large dataset processing

3. **Performance optimization**:
   - Memoization for repeated subproblems
   - Iterative alternatives to recursion
   - Tail recursion optimization techniques

The recursive functions in this budget planner provide a solid foundation for understanding recursion in practical, real-world applications while demonstrating clean code practices and effective problem decomposition strategies.