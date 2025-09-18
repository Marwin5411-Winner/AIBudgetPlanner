import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.chains import LLMChain # Not needed if using LCEL
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate

#Tool imports
from Tools.google_map_search import GoogleMapSearchTool
from Tools.flight_search import FlightSearchTool

# Currency symbols tuple - could be created with comprehension for more complex scenarios
cur_symbols = ("USD", "EUR", "GBP", "INR", "AUD", "CAD", "JPY", "CNY", "RUB", "BRL", "THB")

# Example of how to create currency groups using dictionary comprehension (educational)
currency_groups = {
    'major': [symbol for symbol in cur_symbols if symbol in ["USD", "EUR", "GBP", "JPY"]],
    'emerging': [symbol for symbol in cur_symbols if symbol in ["INR", "CNY", "RUB", "BRL", "THB"]],
    'commonwealth': [symbol for symbol in cur_symbols if symbol in ["AUD", "CAD", "GBP"]]
}

# Timeline Data Structures
@dataclass
class TimelineItem:
    """Represents a single item in the budget timeline"""
    id: str
    title: str
    description: str
    date: str  # YYYY-MM-DD format
    time: str  # HH:MM format
    cost: float
    category: str
    location: str
    duration_hours: float
    booking_required: bool = False
    booking_url: str = ""
    ai_suggested: bool = False
    notes: str = ""

@dataclass
class BudgetTimeline:
    """Main timeline container with budget tracking"""
    items: List[TimelineItem]
    total_budget: float
    currency: str
    start_date: str
    end_date: str
    location: str
    
    @property
    def total_cost(self) -> float:
        return sum(item.cost for item in self.items)
    
    @property
    def remaining_budget(self) -> float:
        return self.total_budget - self.total_cost
    
    @property
    def budget_utilization(self) -> float:
        return (self.total_cost / self.total_budget) * 100 if self.total_budget > 0 else 0

# Constants
NOT_SPECIFIED = "Not specified"

# Timeline Categories
TIMELINE_CATEGORIES = {
    "🍽️ Food & Dining": "#FF6B6B",
    "✈️ Transportation": "#4ECDC4", 
    "🏨 Accommodation": "#45B7D1",
    "🎭 Entertainment": "#96CEB4",
    "🛍️ Shopping": "#FFEAA7",
    "🎯 Activities": "#DDA0DD",
    "📱 Services": "#98D8C8",
    "💼 Business": "#F7DC6F",
    "🏥 Health": "#F8BBD9",
    "📚 Education": "#E8C5E5",
    "🎨 Culture": "#FFB3BA",
    "🌿 Nature": "#B8E6B8"
}

# Recursive Budget Analysis Functions
@dataclass
class BudgetNode:
    """Represents a node in the hierarchical budget tree"""
    name: str
    allocated_budget: float
    actual_cost: float
    children: List['BudgetNode']
    items: List[TimelineItem]
    category: str = ""
    priority_level: int = 1  # 1=highest, 5=lowest

    @property
    def remaining_budget(self) -> float:
        return self.allocated_budget - self.actual_cost
    
    @property
    def utilization_rate(self) -> float:
        return (self.actual_cost / self.allocated_budget * 100) if self.allocated_budget > 0 else 0

def create_hierarchical_budget_tree(timeline: BudgetTimeline, budget_rules: Dict[str, Dict] = None) -> BudgetNode:
    """
    Recursively creates a hierarchical budget breakdown tree from timeline items.
    
    Args:
        timeline: The budget timeline containing all items
        budget_rules: Optional rules for budget allocation percentages
    
    Returns:
        Root BudgetNode representing the entire budget hierarchy
    """
    if budget_rules is None:
        # Default budget allocation rules (percentages of total budget)
        budget_rules = {
            "🍽️ Food & Dining": {"percentage": 0.30, "priority": 2},
            "✈️ Transportation": {"percentage": 0.25, "priority": 1},
            "🏨 Accommodation": {"percentage": 0.25, "priority": 1},
            "🎭 Entertainment": {"percentage": 0.10, "priority": 3},
            "🛍️ Shopping": {"percentage": 0.05, "priority": 4},
            "🎯 Activities": {"percentage": 0.05, "priority": 3}
        }
    
    # Create root node
    root = BudgetNode(
        name="Total Budget",
        allocated_budget=timeline.total_budget,
        actual_cost=timeline.total_cost,
        children=[],
        items=timeline.items,
        category="root"
    )
    
    # Group items by category
    category_items = {}
    for item in timeline.items:
        category = item.category
        if category not in category_items:
            category_items[category] = []
        category_items[category].append(item)
    
    # Create child nodes for each category
    for category, items in category_items.items():
        actual_cost = sum(item.cost for item in items)
        
        # Calculate allocated budget based on rules
        rule = budget_rules.get(category, {"percentage": 0.10, "priority": 3})
        allocated_budget = timeline.total_budget * rule["percentage"]
        
        category_node = BudgetNode(
            name=category,
            allocated_budget=allocated_budget,
            actual_cost=actual_cost,
            children=[],
            items=items,
            category=category,
            priority_level=rule["priority"]
        )
        
        # Recursively create sub-categories based on location or date
        category_node.children = create_budget_subcategories(items, allocated_budget, category)
        root.children.append(category_node)
    
    return root

def create_budget_subcategories(items: List[TimelineItem], parent_budget: float, parent_category: str) -> List[BudgetNode]:
    """
    Recursively creates subcategories for budget items.
    Base case: If fewer than 2 items, no need to subdivide.
    
    Args:
        items: List of timeline items to categorize
        parent_budget: Budget allocated to parent category
        parent_category: Parent category name
    
    Returns:
        List of BudgetNode children representing subcategories
    """
    # Base case: Not enough items to subdivide
    if len(items) <= 1:
        return []
    
    subcategories = []
    
    # Recursive case 1: Group by location if items have different locations
    locations = {}
    for item in items:
        location = item.location if item.location else "Unknown Location"
        if location not in locations:
            locations[location] = []
        locations[location].append(item)
    
    # If we have multiple locations, create location-based subcategories
    if len(locations) > 1:
        for location, location_items in locations.items():
            actual_cost = sum(item.cost for item in location_items)
            # Proportionally allocate budget based on item count
            allocated_budget = parent_budget * (len(location_items) / len(items))
            
            location_node = BudgetNode(
                name=f"{location}",
                allocated_budget=allocated_budget,
                actual_cost=actual_cost,
                children=[],
                items=location_items,
                category=f"{parent_category} - {location}"
            )
            
            # Recursively subdivide by date if we have multiple dates
            location_node.children = create_date_subcategories(location_items, allocated_budget, location_node.category)
            subcategories.append(location_node)
    
    # Recursive case 2: If single location, group by date
    elif len(items) > 2:
        # Group by date
        dates = {}
        for item in items:
            date = item.date
            if date not in dates:
                dates[date] = []
            dates[date].append(item)
        
        if len(dates) > 1:
            for date, date_items in dates.items():
                actual_cost = sum(item.cost for item in date_items)
                allocated_budget = parent_budget * (len(date_items) / len(items))
                
                date_node = BudgetNode(
                    name=f"Day {date}",
                    allocated_budget=allocated_budget,
                    actual_cost=actual_cost,
                    children=[],
                    items=date_items,
                    category=f"{parent_category} - {date}"
                )
                subcategories.append(date_node)
    
    return subcategories

def create_date_subcategories(items: List[TimelineItem], parent_budget: float, parent_category: str) -> List[BudgetNode]:
    """
    Recursively creates date-based subcategories.
    Base case: Single date or fewer than 2 items.
    
    Args:
        items: List of timeline items to categorize by date
        parent_budget: Budget allocated to parent category  
        parent_category: Parent category name
    
    Returns:
        List of BudgetNode children representing date subcategories
    """
    # Base case: Not enough items or all same date
    if len(items) <= 1:
        return []
    
    # Group by date
    dates = {}
    for item in items:
        date = item.date
        if date not in dates:
            dates[date] = []
        dates[date].append(item)
    
    # Base case: All items on same date
    if len(dates) <= 1:
        return []
    
    # Recursive case: Create date subcategories
    subcategories = []
    for date, date_items in dates.items():
        actual_cost = sum(item.cost for item in date_items)
        allocated_budget = parent_budget * (len(date_items) / len(items))
        
        date_node = BudgetNode(
            name=f"{date}",
            allocated_budget=allocated_budget,
            actual_cost=actual_cost,
            children=[],
            items=date_items,
            category=f"{parent_category} - {date}"
        )
        subcategories.append(date_node)
    
    return subcategories

def recursive_budget_optimization(node: BudgetNode, optimization_factor: float = 0.1, depth: int = 0) -> Dict[str, Any]:
    """
    Recursively optimizes budget allocation across the hierarchy.
    
    Args:
        node: Current budget node to optimize
        optimization_factor: Factor for budget reallocation (0.1 = 10%)
        depth: Current recursion depth
    
    Returns:
        Dictionary containing optimization suggestions and statistics
    """
    # Base case: Maximum recursion depth reached or no children
    if depth > 5 or not node.children:
        return {
            "node_name": node.name,
            "current_cost": node.actual_cost,
            "allocated_budget": node.allocated_budget,
            "utilization_rate": node.utilization_rate,
            "suggestions": [],
            "depth": depth
        }
    
    # Recursive case: Analyze children and provide optimization suggestions
    suggestions = []
    child_analyses = []
    
    # Recursively analyze each child
    for child in node.children:
        child_analysis = recursive_budget_optimization(child, optimization_factor, depth + 1)
        child_analyses.append(child_analysis)
        
        # Generate optimization suggestions based on child analysis
        if child.utilization_rate > 120:  # Over budget by 20%
            excess = child.actual_cost - child.allocated_budget
            suggestions.append({
                "type": "over_budget_warning",
                "category": child.name,
                "message": f"{child.name} is over budget by ${excess:.2f}",
                "severity": "high",
                "recommended_action": f"Consider reducing costs in {child.name} or reallocating budget"
            })
        elif child.utilization_rate < 50:  # Under-utilizing budget
            unused = child.allocated_budget - child.actual_cost
            suggestions.append({
                "type": "under_utilization",
                "category": child.name,
                "message": f"{child.name} has ${unused:.2f} unused budget",
                "severity": "medium",
                "recommended_action": f"Consider adding activities in {child.name} or reallocating to other categories"
            })
    
    # Find reallocation opportunities between siblings
    over_budget_children = [child for child in node.children if child.utilization_rate > 100]
    under_budget_children = [child for child in node.children if child.utilization_rate < 80]
    
    if over_budget_children and under_budget_children:
        for over_child in over_budget_children:
            for under_child in under_budget_children:
                potential_transfer = min(
                    over_child.actual_cost - over_child.allocated_budget,
                    under_child.allocated_budget - under_child.actual_cost
                ) * optimization_factor
                
                if potential_transfer > 0:
                    suggestions.append({
                        "type": "reallocation_opportunity",
                        "from_category": under_child.name,
                        "to_category": over_child.name,
                        "amount": potential_transfer,
                        "message": f"Consider reallocating ${potential_transfer:.2f} from {under_child.name} to {over_child.name}",
                        "severity": "low",
                        "recommended_action": f"Transfer budget to optimize spending across categories"
                    })
    
    return {
        "node_name": node.name,
        "current_cost": node.actual_cost,
        "allocated_budget": node.allocated_budget,
        "utilization_rate": node.utilization_rate,
        "suggestions": suggestions,
        "children_analyses": child_analyses,
        "depth": depth,
        "total_suggestions": len(suggestions) + sum(len(child["suggestions"]) for child in child_analyses)
    }

def recursive_timeline_search(timeline_items: List[TimelineItem], search_criteria: Dict[str, Any], depth: int = 0) -> List[TimelineItem]:
    """
    Recursively searches timeline items based on nested criteria.
    
    Args:
        timeline_items: List of timeline items to search
        search_criteria: Dictionary with nested search criteria
        depth: Current recursion depth
    
    Returns:
        List of matching timeline items
    """
    # Base case: No items or maximum depth reached
    if not timeline_items or depth > 3:
        return timeline_items
    
    # Extract current level criteria
    current_criteria = {}
    nested_criteria = {}
    
    for key, value in search_criteria.items():
        if isinstance(value, dict):
            nested_criteria[key] = value
        else:
            current_criteria[key] = value
    
    # Filter by current level criteria
    filtered_items = timeline_items.copy()
    
    for criterion, value in current_criteria.items():
        if criterion == "category":
            filtered_items = [item for item in filtered_items if value.lower() in item.category.lower()]
        elif criterion == "location":
            filtered_items = [item for item in filtered_items if value.lower() in item.location.lower()]
        elif criterion == "date_range":
            start_date, end_date = value
            filtered_items = [item for item in filtered_items if start_date <= item.date <= end_date]
        elif criterion == "cost_range":
            min_cost, max_cost = value
            filtered_items = [item for item in filtered_items if min_cost <= item.cost <= max_cost]
        elif criterion == "duration_range":
            min_duration, max_duration = value
            filtered_items = [item for item in filtered_items if min_duration <= item.duration_hours <= max_duration]
    
    # Base case: No nested criteria, return filtered results
    if not nested_criteria:
        return filtered_items
    
    # Recursive case: Apply nested criteria
    final_results = []
    for nested_key, nested_value in nested_criteria.items():
        if nested_key == "and":
            # Recursive AND operation
            recursive_results = recursive_timeline_search(filtered_items, nested_value, depth + 1)
            final_results = recursive_results if not final_results else list(set(final_results) & set(recursive_results))
        elif nested_key == "or":
            # Recursive OR operation  
            recursive_results = recursive_timeline_search(timeline_items, nested_value, depth + 1)
            final_results.extend(recursive_results)
    
    # Remove duplicates and return
    return list(set(final_results)) if final_results else filtered_items

# Initialize session state for timeline
def init_session_state():
    """Initialize session state variables for timeline management"""
    if 'timeline' not in st.session_state:
        st.session_state.timeline = None
    if 'selected_item_id' not in st.session_state:
        st.session_state.selected_item_id = None
    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = False
    if 'ai_suggestions' not in st.session_state:
        st.session_state.ai_suggestions = []
    if 'budget_tree' not in st.session_state:
        st.session_state.budget_tree = None
    if 'optimization_results' not in st.session_state:
        st.session_state.optimization_results = None

# Define domain-specific sets for set operations demonstration
def create_timeline_chart(timeline: BudgetTimeline) -> go.Figure:
    """Create an interactive timeline chart using Plotly"""
    if not timeline.items:
        return go.Figure()
    
    # Sort items by date and time
    sorted_items = sorted(timeline.items, key=lambda x: f"{x.date} {x.time}")
    
    fig = go.Figure()
    
    # Create datetime objects for proper plotting
    datetimes = [datetime.strptime(f"{item.date} {item.time}", "%Y-%m-%d %H:%M") for item in sorted_items]
    
    # Add timeline items as scatter plot
    for i, item in enumerate(sorted_items):
        color = TIMELINE_CATEGORIES.get(item.category, "#95A5A6")
        
        fig.add_trace(go.Scatter(
            x=[datetimes[i]],
            y=[i],
            mode='markers+text',
            marker={
                'size': 15 + (item.cost / max(it.cost for it in sorted_items) * 10) if sorted_items else 15,
                'color': color,
                'line': {'width': 2, 'color': 'white'}
            },
            text=f"{item.title}<br>${item.cost:.2f}",
            textposition="middle right",
            textfont={'size': 10},
            name=item.category,
            customdata=[item.id],
            hovertemplate=f"<b>{item.title}</b><br>" +
                         f"📅 {item.date} {item.time}<br>" +
                         f"💰 ${item.cost:.2f}<br>" +
                         f"📍 {item.location}<br>" +
                         f"⏱️ {item.duration_hours}h<br>" +
                         f"📝 {item.description}<extra></extra>"
        ))
    
    # Customize layout
    fig.update_layout(
        title=f"Budget Timeline - {timeline.location}",
        xaxis_title="Date & Time",
        yaxis_title="Activities",
        height=500,
        showlegend=False,
        yaxis={'showticklabels': False},
        xaxis={
            'type': 'date',
            'tickformat': '%Y-%m-%d %H:%M'
        },
        hovermode='closest'
    )
    
    return fig

def render_timeline_item_card(item: TimelineItem):
    """Render a timeline item as an interactive card"""
    with st.container():
        col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
        
        with col1:
            # Item title and description
            st.markdown(f"**{item.title}**")
            st.caption(f"{item.description}")
            if item.ai_suggested:
                st.info("🤖 AI Suggested")
        
        with col2:
            # Date, time, and location
            st.text(f"📅 {item.date}")
            st.text(f"⏰ {item.time}")
            st.text(f"📍 {item.location}")
        
        with col3:
            # Cost and category
            st.metric("Cost", f"${item.cost:.2f}")
            st.text(f"🏷️ {item.category.split(' ')[1] if ' ' in item.category else item.category}")
        
        with col4:
            # Action buttons
            if st.button("✏️", key=f"edit_{item.id}", help="Edit item"):
                st.session_state.selected_item_id = item.id
                st.session_state.edit_mode = True
                st.rerun()
            
            if st.button("🗑️", key=f"delete_{item.id}", help="Delete item"):
                if st.session_state.timeline:
                    st.session_state.timeline.items = [i for i in st.session_state.timeline.items if i.id != item.id]
                st.rerun()

def render_timeline_editor():
    """Render the timeline editor interface"""
    if not st.session_state.timeline:
        return
    
    st.header("📅 Interactive Budget Timeline", divider="rainbow")
    
    # Budget overview
    timeline = st.session_state.timeline
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Budget", f"{timeline.currency} {timeline.total_budget:.2f}")
    with col2:
        st.metric("Spent", f"{timeline.currency} {timeline.total_cost:.2f}")
    with col3:
        st.metric("Remaining", f"{timeline.currency} {timeline.remaining_budget:.2f}")
    with col4:
        st.metric("Budget Used", f"{timeline.budget_utilization:.1f}%")
    
    # Budget progress bar
    st.progress(min(timeline.budget_utilization / 100, 1.0))
    
    # Timeline visualization
    if timeline.items:
        st.subheader("📊 Timeline Visualization")
        fig = create_timeline_chart(timeline)
        st.plotly_chart(fig, use_container_width=True)
    
    # Timeline items list
    st.subheader("📋 Timeline Items")
    
    if timeline.items:
        # Sort items by date and time
        sorted_items = sorted(timeline.items, key=lambda x: f"{x.date} {x.time}")
        
        for i, item in enumerate(sorted_items):
            with st.expander(f"{item.title} - {item.date} {item.time} - ${item.cost:.2f}"):
                render_timeline_item_card(item)
    else:
        st.info("No timeline items yet. Use the AI planner to generate your timeline!")

def render_item_editor_form(item: Optional[TimelineItem] = None):
    """Render the basic item editor form fields"""
    col1, col2 = st.columns(2)
    
    with col1:
        title = st.text_input("Title", value=item.title if item else "")
        description = st.text_area("Description", value=item.description if item else "", height=100)
        location = st.text_input("Location", value=item.location if item else "")
        category = st.selectbox("Category", 
                              options=list(TIMELINE_CATEGORIES.keys()),
                              index=list(TIMELINE_CATEGORIES.keys()).index(item.category) if item and item.category in TIMELINE_CATEGORIES else 0)
    
    with col2:
        date = st.date_input("Date", 
                           value=datetime.strptime(item.date, "%Y-%m-%d").date() if item else datetime.now().date())
        time = st.time_input("Time", 
                           value=datetime.strptime(item.time, "%H:%M").time() if item else datetime.now().time())
        cost = st.number_input("Cost", min_value=0.0, value=item.cost if item else 0.0, step=1.0)
        duration = st.number_input("Duration (hours)", min_value=0.1, value=item.duration_hours if item else 1.0, step=0.5)
    
    booking_required = st.checkbox("Booking Required", value=item.booking_required if item else False)
    
    if booking_required:
        booking_url = st.text_input("Booking URL", value=item.booking_url if item else "")
    else:
        booking_url = ""
    
    notes = st.text_area("Notes", value=item.notes if item else "", height=70)
    
    return {
        'title': title,
        'description': description,
        'location': location,
        'category': category,
        'date': date,
        'time': time,
        'cost': cost,
        'duration': duration,
        'booking_required': booking_required,
        'booking_url': booking_url,
        'notes': notes
    }

def render_item_editor(item: Optional[TimelineItem] = None):
    """Render the item editor form"""
    st.subheader("✏️ " + ("Edit Timeline Item" if item else "Add New Timeline Item"))
    
    # Form for editing/adding items
    with st.form("item_editor"):
        form_data = render_item_editor_form(item)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.form_submit_button("💾 Save", type="primary"):
                # Create or update item
                new_item = TimelineItem(
                    id=item.id if item else f"item_{datetime.now().timestamp()}",
                    title=form_data['title'],
                    description=form_data['description'],
                    date=form_data['date'].strftime("%Y-%m-%d"),
                    time=form_data['time'].strftime("%H:%M"),
                    cost=form_data['cost'],
                    category=form_data['category'],
                    location=form_data['location'],
                    duration_hours=form_data['duration'],
                    booking_required=form_data['booking_required'],
                    booking_url=form_data['booking_url'],
                    notes=form_data['notes']
                )
                
                if item:  # Update existing
                    if st.session_state.timeline:
                        st.session_state.timeline.items = [
                            new_item if i.id == item.id else i 
                            for i in st.session_state.timeline.items
                        ]
                else:  # Add new
                    if st.session_state.timeline:
                        st.session_state.timeline.items.append(new_item)
                
                st.session_state.edit_mode = False
                st.session_state.selected_item_id = None
                st.success("Item saved successfully!")
                st.rerun()
        
        with col2:
            if st.form_submit_button("❌ Cancel"):
                st.session_state.edit_mode = False
                st.session_state.selected_item_id = None
                st.rerun()
        
        with col3:
            if item and st.form_submit_button("🗑️ Delete", type="secondary"):
                if st.session_state.timeline:
                    st.session_state.timeline.items = [i for i in st.session_state.timeline.items if i.id != item.id]
                st.session_state.edit_mode = False
                st.session_state.selected_item_id = None
                st.success("Item deleted!")
                st.rerun()

def get_domain_sets():
    """Returns three sets related to budget planning domain using advanced comprehensions"""
    
    # Base destination data with categories
    destinations_data = {
        "Paris": ["popular", "budget"],
        "Tokyo": ["popular", "adventure"],
        "New York": ["popular", "budget"],
        "Bangkok": ["popular", "budget", "adventure"],
        "London": ["popular"],
        "Sydney": ["popular"],
        "Rome": ["popular"],
        "Barcelona": ["popular"],
        "Budapest": ["budget"],
        "Prague": ["budget"],
        "Mexico City": ["budget"],
        "Warsaw": ["budget"],
        "Lisbon": ["budget"],
        "Athens": ["budget"],
        "Nepal": ["adventure"],
        "New Zealand": ["adventure"],
        "Costa Rica": ["adventure"],
        "Iceland": ["adventure"],
        "Peru": ["adventure"],
        "Patagonia": ["adventure"]
    }
    
    # Using dictionary comprehension and set comprehension to create category sets
    category_sets = {
        category: {destination for destination, categories in destinations_data.items() 
                  if category in categories}
        for category in ["popular", "budget", "adventure"]
    }
    
    # Return the sets using tuple unpacking from dictionary comprehension
    return category_sets["popular"], category_sets["budget"], category_sets["adventure"]

def perform_set_operations(set_a, set_b, set_c):
    """Performs all required set operations and returns results"""
    # Using dictionary comprehension to create results with operation mappings
    operations = {
        'union': lambda: set_a.union(set_b).union(set_c),
        'intersection': lambda: set_a.intersection(set_b).intersection(set_c),
        'difference_a_b': lambda: set_a.difference(set_b),
        'difference_c_a': lambda: set_c.difference(set_a),
        'symmetric_diff_a_b': lambda: set_a.symmetric_difference(set_b),
        'is_subset_b_a': lambda: set_b.issubset(set_a),
        'is_superset_a_c': lambda: set_a.issuperset(set_c)
    }
    
    # Dictionary comprehension to execute all operations
    results = {key: operation() for key, operation in operations.items()}
    
    return results



# --- Page Configuration ---
st.set_page_config(page_title="AI Budget Timeline Planner", layout="wide", initial_sidebar_state="expanded")

# Initialize session state
init_session_state()

st.title("� AI Budget Timeline Planner")
st.caption("Create interactive timeline-based budget plans with AI assistance. Add, edit, and optimize your activities with real-time budget tracking.")

# --- API Key Management ---
try:
    if hasattr(st, 'secrets') and "GOOGLE_API_KEY" in st.secrets:
        GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    else:
        GOOGLE_API_KEY = None
except Exception: 
    GOOGLE_API_KEY = None

if not GOOGLE_API_KEY:
    GOOGLE_API_KEY = st.sidebar.text_input(
        "Enter your Google API Key:",
        type="password",
        help="Get your API key from Google AI Studio. The app requires this key to function.",
        key="google_api_key_input_sidebar"
    )
    
    GOOGLE_MAPS_API_KEY = st.sidebar.text_input(
        "Enter your Google Maps API Key:",
        type="password",
        help="Get your API key from Google Cloud Console. The app requires this key to search for places.",
        key="google_maps_api_key_input_sidebar"
    )
    
    st.sidebar.info("""
    **✈️ Flight Search Available!**
    
    This app now supports real flight search powered by Google Flights. You can include flight bookings in your budget plans by specifying:
    - Departure and destination airports (IATA codes like LAX, JFK, CDG)
    - Travel dates in YYYY-MM-DD format
    - Trip type (one-way or round-trip)
    - Number of passengers and seat class
    
    Example: "Round-trip flight from LAX to JFK on 2025-08-15 returning 2025-08-20"
    """)

else:
    st.sidebar.success("✅ API Keys configured!")
    st.sidebar.info("""
    **✈️ Flight Search Ready!**
    
    Include flights in your budget by specifying:
    - Airport codes (LAX, JFK, CDG, etc.)
    - Dates (YYYY-MM-DD format)
    - Trip details (one-way/round-trip)
    """)

# Only show Google Maps API input if Google API key is provided
# if GOOGLE_API_KEY and not GOOGLE_MAPS_API_KEY:
#     GOOGLE_MAPS_API_KEY = st.sidebar.text_input(
#         "Enter your Google Maps API Key:",
#         type="password",
#         help="Get your API key from Google Cloud Console. This is only needed for local place searches.",
#         key="google_maps_api_key_input_sidebar_conditional"
#     )

# --- Debug Mode Toggle ---
st.sidebar.markdown("---")
st.sidebar.subheader("🔧 Developer Settings")
st.session_state.show_debug = st.sidebar.checkbox(
    "Enable Debug Mode",
    value=st.session_state.get('show_debug', False),
    help="Show AI agent scratchpad and debugging information"
)

if st.session_state.show_debug:
    st.sidebar.info("🐛 Debug mode enabled. Agent scratchpad will be visible in AI suggestions.")
    
    # Clear debug history button
    if st.sidebar.button("🗑️ Clear Debug History"):
        st.session_state.agent_scratchpad_debug = []
        st.sidebar.success("Debug history cleared!")

# --- Langchain Setup ---
llm = None
budget_agent_executor = None 

if GOOGLE_API_KEY:
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=GOOGLE_API_KEY,
            temperature=0.5,
            convert_system_message_to_human=True
        )

        # Initialize tools using list comprehension for conditional tool addition
        tools = [FlightSearchTool()]  # Always include flight search tool
        
        # Add Google Maps tool only if API key is available using conditional list comprehension
        tools.extend([GoogleMapSearchTool(api_key=GOOGLE_MAPS_API_KEY)] if GOOGLE_MAPS_API_KEY else [])

        
        # Agent prompt template with dynamic tool availability
        available_tools_info = "FlightSearch (for flight bookings)"
        if GOOGLE_MAPS_API_KEY:
            available_tools_info += " and GoogleMapSearch (for local places)"
        
        agent_prompt = ChatPromptTemplate.from_messages([
            ("system", f"""You are a friendly, insightful, and practical AI budget planner that creates structured timeline-based budget plans.
            You have access to these tools: {available_tools_info}.
            
            IMPORTANT: You MUST return a JSON structure for timeline-based budget planning, not just text!
            
            The user has a total budget of {{currency}}{{budget}}.
            The user is located in {{location}} (if provided).
            The user wants to engage in the following activities: {{activities}}.

            RESPONSE FORMAT:
            You must return a JSON object with this exact structure:
            {{{{
                "timeline_items": [
                    {{{{
                        "title": "Activity Name",
                        "description": "Brief description",
                        "date": "YYYY-MM-DD",
                        "time": "HH:MM",
                        "cost": 50.00,
                        "category": "🍽️ Food & Dining",
                        "location": "Specific location",
                        "duration_hours": 2.0,
                        "booking_required": true,
                        "booking_url": "https://...",
                        "ai_suggested": true,
                        "notes": "Additional notes"
                    }}}}
                ],
                "budget_analysis": {{{{
                    "total_cost": 150.00,
                    "remaining_budget": 50.00,
                    "feasibility": "Within budget",
                    "recommendations": ["Tip 1", "Tip 2"]
                }}}},
                "ai_suggestions": [
                    {{{{
                        "type": "cost_optimization",
                        "suggestion": "Consider lunch instead of dinner to save $20",
                        "potential_savings": 20.00
                    }}}}
                ]
            }}}}

            CATEGORIES TO USE:
            🍽️ Food & Dining, ✈️ Transportation, 🏨 Accommodation, 🎭 Entertainment, 
            🛍️ Shopping, 🎯 Activities, 📱 Services, 💼 Business, 🏥 Health, 
            📚 Education, 🎨 Culture, 🌿 Nature

            STEP-BY-STEP PROCESS:
            1. For EACH activity mentioned by the user, call the appropriate tool to get real data
            2. Create timeline items with realistic dates, times, and costs
            3. Ensure activities are scheduled logically (chronological order, realistic timing)
            4. Calculate total costs and provide budget analysis
            5. Suggest optimizations if over budget
            
            Remember: ALWAYS use the available tools for real data, then format as JSON!"""),
            ("human", """Create a detailed timeline-based budget plan for:

Budget: {currency}{budget}
Location: {location}
Activities: {activities}

IMPORTANT: 
1. Use the appropriate tools to find real information for each activity
2. Return the response as a structured JSON format for timeline creation
3. Include realistic dates, times, and locations
4. Provide cost breakdowns and budget analysis
5. Suggest optimizations if needed

Generate a comprehensive timeline-based budget plan in JSON format."""),
            ("placeholder", "{agent_scratchpad}")
        ])

        # Create the agent
        agent = create_tool_calling_agent(llm, tools, agent_prompt)
        
        # Create the agent executor with more debugging
        budget_agent_executor = AgentExecutor(
            agent=agent, 
            tools=tools, 
            verbose=True,  # Enable verbose mode to see tool calls
            max_iterations=20,
            return_intermediate_steps=True,  # Enable to capture scratchpad data
            handle_parsing_errors=True,
            early_stopping_method="generate"  # Ensures complete response generation
        )

    except Exception as e:
        st.sidebar.error(f"Error initializing AI model: {e}")
        st.toast(f"Error initializing AI: {e}", icon="❌")

else:
    st.sidebar.warning("Please enter your Google API Key in the sidebar to enable the AI planner.")
    st.sidebar.info("💡 The flight search tool will work with just the Google API Key. Google Maps API is optional for local place searches.")

def parse_ai_response_to_timeline(ai_response: str, budget: float, currency: str, location: str) -> BudgetTimeline:
    """Parse AI response and create a BudgetTimeline object"""
    try:
        # Try to extract JSON from the response
        import re
        json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
        if json_match:
            response_data = json.loads(json_match.group())
        else:
            # Fallback: create a simple timeline from text
            return create_fallback_timeline(ai_response, budget, currency, location)
        
        # Create timeline items from AI response
        timeline_items = []
        for item_data in response_data.get('timeline_items', []):
            timeline_item = TimelineItem(
                id=f"ai_item_{datetime.now().timestamp()}_{len(timeline_items)}",
                title=item_data.get('title', 'Untitled Activity'),
                description=item_data.get('description', ''),
                date=item_data.get('date', datetime.now().strftime('%Y-%m-%d')),
                time=item_data.get('time', '09:00'),
                cost=float(item_data.get('cost', 0)),
                category=item_data.get('category', '🎯 Activities'),
                location=item_data.get('location', location),
                duration_hours=float(item_data.get('duration_hours', 1.0)),
                booking_required=item_data.get('booking_required', False),
                booking_url=item_data.get('booking_url', ''),
                ai_suggested=True,
                notes=item_data.get('notes', '')
            )
            timeline_items.append(timeline_item)
        
        # Create the timeline
        timeline = BudgetTimeline(
            items=timeline_items,
            total_budget=budget,
            currency=currency,
            start_date=min(item.date for item in timeline_items) if timeline_items else datetime.now().strftime('%Y-%m-%d'),
            end_date=max(item.date for item in timeline_items) if timeline_items else datetime.now().strftime('%Y-%m-%d'),
            location=location
        )
        
        # Store AI suggestions in session state
        if 'ai_suggestions' in response_data:
            st.session_state.ai_suggestions = response_data['ai_suggestions']
        
        return timeline
        
    except json.JSONDecodeError as e:
        st.warning(f"Could not parse AI response as JSON. Creating fallback timeline. Error: {e}")
        return create_fallback_timeline(ai_response, budget, currency, location)

def create_fallback_timeline(ai_response: str, budget: float, currency: str, location: str) -> BudgetTimeline:
    """Create a basic timeline when AI response parsing fails"""
    # Create a simple timeline item from the AI response
    timeline_item = TimelineItem(
        id=f"fallback_{datetime.now().timestamp()}",
        title="AI Generated Plan",
        description=ai_response[:200] + "..." if len(ai_response) > 200 else ai_response,
        date=datetime.now().strftime('%Y-%m-%d'),
        time='09:00',
        cost=budget * 0.8,  # Use 80% of budget as estimate
        category='🎯 Activities',
        location=location,
        duration_hours=4.0,
        booking_required=False,
        booking_url='',
        ai_suggested=True,
        notes=ai_response
    )
    
    return BudgetTimeline(
        items=[timeline_item],
        total_budget=budget,
        currency=currency,
        start_date=datetime.now().strftime('%Y-%m-%d'),
        end_date=datetime.now().strftime('%Y-%m-%d'),
        location=location
    )

def format_agent_step(step):
    """Format an agent intermediate step for display"""
    if isinstance(step, tuple) and len(step) == 2:
        action, observation = step
        
        # Format the action
        if hasattr(action, 'tool') and hasattr(action, 'tool_input'):
            action_text = f"**Tool:** {action.tool}\n**Input:** {action.tool_input}"
        else:
            action_text = str(action)
            
        # Format the observation
        observation_text = str(observation)[:300] + "..." if len(str(observation)) > 300 else str(observation)
        
        return f"**Action:**\n{action_text}\n\n**Observation:**\n{observation_text}"
    else:
        return str(step)[:300] + "..." if len(str(step)) > 300 else str(step)

def render_ai_suggestions():
    """Render AI suggestions panel"""
    if st.session_state.ai_suggestions:
        st.subheader("🤖 AI Suggestions")
        
        # Show budget analysis if available
        if hasattr(st.session_state, 'budget_analysis') and st.session_state.budget_analysis:
            budget_status = st.session_state.budget_analysis.get('status', 'unknown')
            if budget_status == 'over_budget':
                st.error("⚠️ You're over budget! Consider the suggestions below.")
            elif budget_status == 'within_budget':
                st.success("✅ You're within budget. Great job!")
            elif budget_status == 'under_budget':
                st.info("💡 You have budget remaining. Consider adding more activities!")
            
            # Show general recommendations
            recommendations = st.session_state.budget_analysis.get('recommendations', [])
            if recommendations:
                st.write("**General Recommendations:**")
                for rec in recommendations:
                    st.write(f"• {rec}")
        
        # Organize suggestions by priority
        high_priority = [s for s in st.session_state.ai_suggestions if s.get('priority') == 'high']
        medium_priority = [s for s in st.session_state.ai_suggestions if s.get('priority') == 'medium']
        low_priority = [s for s in st.session_state.ai_suggestions if s.get('priority') == 'low']
        
        # Display suggestions by priority
        for priority_group, priority_name, color in [
            (high_priority, "High Priority", "🔴"),
            (medium_priority, "Medium Priority", "🟡"), 
            (low_priority, "Low Priority", "🟢")
        ]:
            if priority_group:
                st.write(f"**{color} {priority_name} Suggestions:**")
                
                for i, suggestion in enumerate(priority_group):
                    suggestion_type = suggestion.get('type', 'suggestion').replace('_', ' ').title()
                    
                    with st.expander(f"💡 {suggestion_type}"):
                        st.write(suggestion.get('suggestion', 'No suggestion text available'))
                        
                        # Show potential savings
                        if 'potential_savings' in suggestion and suggestion['potential_savings'] > 0:
                            st.success(f"💰 Potential savings: {st.session_state.timeline.currency if st.session_state.timeline else '$'}{suggestion['potential_savings']:.2f}")
                        
                        # Show affected items
                        if 'affected_items' in suggestion and suggestion['affected_items']:
                            st.write("**Affects these items:**")
                            for item in suggestion['affected_items']:
                                st.write(f"• {item}")
                        
                        # Action buttons
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("✅ Apply Suggestion", key=f"apply_suggestion_{priority_name}_{i}"):
                                st.info("💫 Auto-apply feature coming soon! For now, manually adjust your timeline items.")
                        
                        with col2:
                            if st.button("❌ Dismiss", key=f"dismiss_suggestion_{priority_name}_{i}"):
                                # Remove this suggestion
                                st.session_state.ai_suggestions.remove(suggestion)
                                st.rerun()
    
    # Add agent scratchpad debugging section
    if st.session_state.get('show_debug', False) and st.session_state.get('agent_scratchpad_debug'):
        with st.expander("🔧 Agent Debug Info (Developer Mode)"):
            st.subheader("Agent Scratchpad History")
            
            for i, debug_info in enumerate(reversed(st.session_state.agent_scratchpad_debug[-5:])):  # Show last 5
                st.write(f"**Debug Session {len(st.session_state.agent_scratchpad_debug) - i}** - {debug_info['timestamp']}")
                st.write(f"Type: {debug_info['type']}")
                
                # Show debug metadata
                if debug_info.get('num_intermediate_steps') is not None:
                    st.write(f"Intermediate Steps Found: {debug_info['num_intermediate_steps']}")
                if debug_info.get('raw_response_keys'):
                    st.write(f"Response Keys: {debug_info['raw_response_keys']}")
                
                with st.expander(f"Input/Output {len(st.session_state.agent_scratchpad_debug) - i}"):
                    st.write("**Input:**")
                    st.code(debug_info['input'][:500] + "..." if len(debug_info['input']) > 500 else debug_info['input'])
                    
                    st.write("**Output:**")
                    st.code(debug_info['output'][:500] + "..." if len(debug_info['output']) > 500 else debug_info['output'])
                    
                    if debug_info.get('intermediate_steps'):
                        st.write(f"**Intermediate Steps ({len(debug_info['intermediate_steps'])} steps):**")
                        for j, step in enumerate(debug_info['intermediate_steps']):
                            with st.expander(f"Step {j+1}"):
                                st.markdown(format_agent_step(step))
                    else:
                        st.warning("⚠️ No intermediate steps captured. This might indicate the agent didn't use any tools or there's an issue with step capturing.")

def render_timeline_export():
    """Render timeline export options"""
    if st.session_state.timeline and st.session_state.timeline.items:
        st.subheader("📤 Export Timeline")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 Export as CSV"):
                # Create DataFrame from timeline items
                items_data = [asdict(item) for item in st.session_state.timeline.items]
                df = pd.DataFrame(items_data)
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=f"budget_timeline_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
        
        with col2:
            if st.button("📋 Export as JSON"):
                timeline_data = {
                    'timeline': asdict(st.session_state.timeline),
                    'export_date': datetime.now().isoformat(),
                    'app_version': '2.0'
                }
                json_str = json.dumps(timeline_data, indent=2)
                st.download_button(
                    label="📥 Download JSON",
                    data=json_str,
                    file_name=f"budget_timeline_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json"
                )
        
        with col3:
            if st.button("🎨 Generate PDF Report"):
                st.info("PDF export feature coming soon! For now, use the browser's print function.")

# --- User Input Area ---
st.header("Step 1: Your Budget Details", divider="rainbow")
col1, col2 = st.columns([1, 2])

with col1:
    bi = st.number_input(
        "💰 Enter your total budget:",
        min_value=0.0,
        step=10.0,
        value=200.0,
        help="Specify your total available budget for the listed activities."
    )
    
    # Update existing timeline budget if it exists and budget changed
    if st.session_state.timeline and st.session_state.timeline.total_budget != bi:
        st.session_state.timeline.total_budget = bi
    
    cs = st.selectbox(
        "💵 Select your currency:",
        options=cur_symbols,
        index=0,
        help="Choose the currency in which your budget is denominated."
    )
    
    # Update existing timeline currency if it exists and currency changed
    if st.session_state.timeline and st.session_state.timeline.currency != cs:
        st.session_state.timeline.currency = cs
    
    li = st.text_input(
        "📍 Enter your location (optional):",
        placeholder="e.g., New York, USA",
        help="Specify your location to tailor the budget plan to local costs."
    )

with col2:
    e_a = "Round-trip flight from LAX to JFK on 2025-08-15 returning 2025-08-20, 3 restaurant meals in New York, visit Central Park attractions, 2 Broadway show tickets"
    act_i = st.text_area(
        "📝 List desired activities:",
        height=120,
        placeholder=f"e.g., {e_a}",
        help="List all activities you want to budget for. For flights, include departure/destination airports and dates. Be as specific as possible."
    )

# --- Generate Plan Button ---
st.header("Step 2: Generate Your Timeline", divider="rainbow")

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("✨ Generate AI Timeline", type="primary", use_container_width=True):
        if not GOOGLE_API_KEY or not budget_agent_executor:
            st.error("AI Model not initialized. Please ensure your Google API Key is correctly entered.")
            st.toast("API Key or AI Model issue.", icon="🔑")
        elif bi <= 0:
            st.warning("Please enter a budget amount greater than zero.")
            st.toast("Budget must be positive.", icon="⚠️")
        elif not act_i.strip():
            st.warning("Please list some activities you'd like to plan for.")
            st.toast("Activities list is empty.", icon="⚠️")
        else:
            with st.spinner("🤖 AI is creating your interactive timeline... Please wait."):
                try:
                    inputs = {
                        "budget": bi, 
                        "activities": act_i, 
                        "location": li or NOT_SPECIFIED, 
                        "currency": cs
                    }
                    
                    ai_response = budget_agent_executor.invoke(inputs)
                    output = ai_response.get("output", str(ai_response))
                    
                    # Store the raw agent response for debugging
                    if 'agent_scratchpad_debug' not in st.session_state:
                        st.session_state.agent_scratchpad_debug = []
                    
                    # Enhanced debugging information
                    debug_entry = {
                        'timestamp': datetime.now().isoformat(),
                        'type': 'timeline_generation',
                        'input': f"Budget: {cs}{bi}, Activities: {act_i}, Location: {li}",
                        'output': output,
                        'intermediate_steps': ai_response.get('intermediate_steps', []),
                        'raw_response_keys': list(ai_response.keys()) if isinstance(ai_response, dict) else 'not_dict',
                        'has_intermediate_steps': 'intermediate_steps' in ai_response,
                        'num_intermediate_steps': len(ai_response.get('intermediate_steps', []))
                    }
                    
                    st.session_state.agent_scratchpad_debug.append(debug_entry)
                    
                    # Debug output in console if debug mode is on
                    if st.session_state.get('show_debug', False):
                        st.write(f"🐛 **Debug Info:** Found {debug_entry['num_intermediate_steps']} intermediate steps")
                    
                    # Parse the AI response into a timeline
                    timeline = parse_ai_response_to_timeline(output, bi, cs, li or NOT_SPECIFIED)
                    st.session_state.timeline = timeline
                    
                    st.success("🎉 Timeline generated successfully!")
                    st.toast("Timeline created!", icon="✅")
                    st.rerun()

                except Exception as e:
                    st.error(f"An error occurred while generating the timeline: {e}")
                    st.toast(f"Generation error: {e}", icon="❌")

with col2:
    if st.button("➕ Add Manual Item", use_container_width=True):
        if not st.session_state.timeline:
            # Create empty timeline if none exists
            st.session_state.timeline = BudgetTimeline(
                items=[],
                total_budget=bi,
                currency=cs,
                start_date=datetime.now().strftime('%Y-%m-%d'),
                end_date=datetime.now().strftime('%Y-%m-%d'),
                location=li or NOT_SPECIFIED
            )
        st.session_state.edit_mode = True
        st.session_state.selected_item_id = None
        st.rerun()

with col3:
    if st.button("🤖 Get AI Suggestions", use_container_width=True):
        if st.session_state.timeline and budget_agent_executor:
            with st.spinner("Getting AI suggestions..."):
                try:
                    # Calculate current statistics
                    total_cost = sum(item.cost for item in st.session_state.timeline.items)
                    remaining_budget = st.session_state.timeline.total_budget - total_cost
                    
                    suggestion_prompt = f"""
                    Analyze the current budget timeline and provide specific optimization suggestions in JSON format.
                    
                    Current Timeline:
                    - Total items: {len(st.session_state.timeline.items)}
                    - Total budget: {cs}{bi}
                    - Current cost: {cs}{total_cost:.2f}
                    - Remaining budget: {cs}{remaining_budget:.2f}
                    - Location: {st.session_state.timeline.location}
                    
                    Items:
                    {chr(10).join([f"- {item.title}: {cs}{item.cost:.2f} on {item.date} ({item.category})" for item in st.session_state.timeline.items])}
                    
                    Return JSON with this structure:
                    {{
                        "suggestions": [
                            {{
                                "type": "cost_optimization|budget_reallocation|activity_suggestion|time_optimization",
                                "suggestion": "Specific actionable suggestion",
                                "potential_savings": 25.50,
                                "affected_items": ["item_title1", "item_title2"],
                                "priority": "high|medium|low"
                            }}
                        ],
                        "budget_analysis": {{
                            "status": "over_budget|within_budget|under_budget",
                            "recommendations": ["recommendation1", "recommendation2"]
                        }}
                    }}
                    """
                    
                    inputs = {
                        "budget": bi,
                        "activities": suggestion_prompt,
                        "location": st.session_state.timeline.location,
                        "currency": cs
                    }
                    
                    suggestion_response = budget_agent_executor.invoke(inputs)
                    output = suggestion_response.get("output", str(suggestion_response))
                    
                    # Store the raw agent response for debugging
                    if 'agent_scratchpad_debug' not in st.session_state:
                        st.session_state.agent_scratchpad_debug = []
                    
                    # Enhanced debugging information
                    debug_entry = {
                        'timestamp': datetime.now().isoformat(),
                        'type': 'ai_suggestions',
                        'input': suggestion_prompt,
                        'output': output,
                        'intermediate_steps': suggestion_response.get('intermediate_steps', []),
                        'raw_response_keys': list(suggestion_response.keys()) if isinstance(suggestion_response, dict) else 'not_dict',
                        'has_intermediate_steps': 'intermediate_steps' in suggestion_response,
                        'num_intermediate_steps': len(suggestion_response.get('intermediate_steps', []))
                    }
                    
                    st.session_state.agent_scratchpad_debug.append(debug_entry)
                    
                    # Debug output in console if debug mode is on
                    if st.session_state.get('show_debug', False):
                        st.write(f"🐛 **Debug Info:** Found {debug_entry['num_intermediate_steps']} intermediate steps")
                    
                    # Parse AI suggestions
                    try:
                        import re
                        json_match = re.search(r'\{.*\}', output, re.DOTALL)
                        if json_match:
                            suggestions_data = json.loads(json_match.group())
                            st.session_state.ai_suggestions = suggestions_data.get('suggestions', [])
                            st.session_state.budget_analysis = suggestions_data.get('budget_analysis', {})
                        else:
                            # Fallback suggestions if JSON parsing fails
                            st.session_state.ai_suggestions = [
                                {
                                    "type": "general_optimization",
                                    "suggestion": output[:200] + "..." if len(output) > 200 else output,
                                    "potential_savings": 0.0,
                                    "priority": "medium"
                                }
                            ]
                    except json.JSONDecodeError:
                        st.session_state.ai_suggestions = [
                            {
                                "type": "parsing_error", 
                                "suggestion": "Could not parse AI response. Raw response: " + output[:100],
                                "priority": "low"
                            }
                        ]
                    
                    st.toast("AI suggestions updated!", icon="💡")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error getting suggestions: {e}")
                    st.toast(f"Suggestion error: {e}", icon="❌")
        else:
            st.warning("Create a timeline first to get AI suggestions!")

# --- Main Timeline Interface ---
st.header("Step 3: Your Interactive Timeline", divider="rainbow")

# Handle edit mode
if st.session_state.edit_mode:
    selected_item = None
    if st.session_state.selected_item_id and st.session_state.timeline:
        selected_item = next((item for item in st.session_state.timeline.items if item.id == st.session_state.selected_item_id), None)
    
    render_item_editor(selected_item)
    
    st.markdown("---")

# Show timeline if exists
if st.session_state.timeline:
    render_timeline_editor()
    
    # AI Suggestions Panel
    if st.session_state.ai_suggestions:
        render_ai_suggestions()
    
    # Export Options
    render_timeline_export()
else:
    # Welcome message when no timeline exists
    st.info("""
    👋 **Welcome to AI Budget Timeline Planner!**
    
    This app helps you create interactive, timeline-based budget plans with AI assistance.
    
    **Features:**
    - 📅 Visual timeline of your activities
    - 💰 Real-time budget tracking
    - ✏️ Click to edit any timeline item
    - 🤖 AI-powered suggestions and optimizations
    - 📊 Export your timeline as CSV or JSON
    - ✈️ Real flight search integration
    - 📍 Google Maps place search
    
    **Get Started:**
    1. Enter your budget and location above
    2. List the activities you want to plan
    3. Click "Generate AI Timeline" to create your plan
    4. Edit, add, or optimize items as needed
    
    *Start by filling in your budget details and clicking the "Generate AI Timeline" button!*
    """)

# --- Recursive Budget Analysis Section ---
if st.session_state.timeline and st.session_state.timeline.items:
    st.header("🔄 Recursive Budget Analysis", divider="green")
    st.caption("Explore hierarchical budget breakdowns and optimization using recursive algorithms")
    
    with st.expander("🌳 Hierarchical Budget Tree Analysis", expanded=False):
        st.markdown("""
        This section demonstrates **recursive algorithms** applied to budget planning:
        - **Hierarchical Budget Breakdown**: Recursively creates nested budget categories
        - **Optimization Analysis**: Recursively optimizes budget allocation across categories  
        - **Timeline Search**: Recursively searches items with nested criteria
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🌲 Generate Budget Tree", key="generate_tree_btn"):
                with st.spinner("Building hierarchical budget tree..."):
                    st.session_state.budget_tree = create_hierarchical_budget_tree(st.session_state.timeline)
                st.success("Budget tree generated!")
                st.rerun()
        
        with col2:
            if st.button("⚡ Optimize Budget Recursively", key="optimize_budget_btn"):
                if st.session_state.budget_tree:
                    with st.spinner("Running recursive optimization..."):
                        optimization_factor = 0.15  # 15% reallocation factor
                        st.session_state.optimization_results = recursive_budget_optimization(
                            st.session_state.budget_tree, 
                            optimization_factor
                        )
                    st.success("Optimization complete!")
                    st.rerun()
                else:
                    st.warning("Generate budget tree first!")
        
        # Display budget tree if available
        if st.session_state.budget_tree:
            st.subheader("🌳 Hierarchical Budget Breakdown")
            
            def render_budget_node(node: BudgetNode, level: int = 0):
                """Recursively renders budget tree nodes in the UI"""
                # Base case: Maximum display depth
                if level > 3:
                    return
                
                # Indent based on hierarchy level  
                indent = "  " * level
                emoji = "🌟" if level == 0 else "📁" if level == 1 else "📄"
                
                # Color-code based on utilization rate
                if node.utilization_rate > 120:
                    status_color = "🔴"
                elif node.utilization_rate > 100:
                    status_color = "🟡"
                elif node.utilization_rate < 50:
                    status_color = "🔵"  
                else:
                    status_color = "🟢"
                
                # Display node information
                st.markdown(f"{indent}{emoji} **{node.name}** {status_color}")
                st.markdown(f"{indent}   💰 Budget: ${node.allocated_budget:.2f} | Spent: ${node.actual_cost:.2f}")
                st.markdown(f"{indent}   📊 Utilization: {node.utilization_rate:.1f}% | Items: {len(node.items)}")
                
                # Recursive case: Render children
                if node.children:
                    for child in node.children:
                        render_budget_node(child, level + 1)
            
            render_budget_node(st.session_state.budget_tree)
            
            # Display tree statistics
            def calculate_tree_stats(node: BudgetNode) -> Dict[str, int]:
                """Recursively calculates statistics for the budget tree"""
                # Base case: Leaf node
                if not node.children:
                    return {
                        "total_nodes": 1,
                        "leaf_nodes": 1, 
                        "max_depth": 0,
                        "over_budget_nodes": 1 if node.utilization_rate > 100 else 0
                    }
                
                # Recursive case: Aggregate children statistics
                stats = {
                    "total_nodes": 1,
                    "leaf_nodes": 0,
                    "max_depth": 0,
                    "over_budget_nodes": 1 if node.utilization_rate > 100 else 0
                }
                
                for child in node.children:
                    child_stats = calculate_tree_stats(child)
                    stats["total_nodes"] += child_stats["total_nodes"]
                    stats["leaf_nodes"] += child_stats["leaf_nodes"]
                    stats["max_depth"] = max(stats["max_depth"], child_stats["max_depth"] + 1)
                    stats["over_budget_nodes"] += child_stats["over_budget_nodes"]
                
                return stats
            
            tree_stats = calculate_tree_stats(st.session_state.budget_tree)
            
            st.markdown("#### 📈 Tree Statistics")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Nodes", tree_stats["total_nodes"])
            col2.metric("Leaf Nodes", tree_stats["leaf_nodes"])
            col3.metric("Max Depth", tree_stats["max_depth"])
            col4.metric("Over Budget", tree_stats["over_budget_nodes"])
        
        # Display optimization results if available
        if st.session_state.optimization_results:
            st.subheader("⚡ Recursive Optimization Results")
            
            def render_optimization_results(results: Dict[str, Any], level: int = 0):
                """Recursively renders optimization results"""
                # Base case: Maximum display depth
                if level > 3:
                    return
                
                indent = "  " * level
                st.markdown(f"{indent}**{results['node_name']}** (Depth {results['depth']})")
                st.markdown(f"{indent}💰 Budget: ${results['allocated_budget']:.2f} | Actual: ${results['current_cost']:.2f}")
                st.markdown(f"{indent}📊 Utilization: {results['utilization_rate']:.1f}%")
                
                # Display suggestions for this node
                if results.get('suggestions'):
                    st.markdown(f"{indent}💡 **Suggestions:**")
                    for suggestion in results['suggestions']:
                        severity_emoji = {"high": "🔥", "medium": "⚠️", "low": "💡"}
                        emoji = severity_emoji.get(suggestion['severity'], "💡")
                        st.markdown(f"{indent}  {emoji} {suggestion['message']}")
                
                # Recursive case: Render children results
                if results.get('children_analyses'):
                    for child_result in results['children_analyses']:
                        render_optimization_results(child_result, level + 1)
            
            render_optimization_results(st.session_state.optimization_results)
            
            # Summary statistics
            total_suggestions = st.session_state.optimization_results.get('total_suggestions', 0)
            if total_suggestions > 0:
                st.success(f"🎯 Generated {total_suggestions} optimization suggestions across all budget categories!")
            else:
                st.info("✅ Budget allocation looks optimal! No major adjustments needed.")
    
    # Recursive Timeline Search Demo
    with st.expander("🔍 Recursive Timeline Search", expanded=False):
        st.markdown("**Demonstrate recursive search with nested criteria:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Search Criteria")
            search_category = st.selectbox("Category contains:", 
                                         options=["", "Food", "Transport", "Entertainment", "Activities"],
                                         key="search_category")
            
            search_location = st.text_input("Location contains:", key="search_location")
            
            cost_min = st.number_input("Min cost:", min_value=0.0, value=0.0, key="cost_min")
            cost_max = st.number_input("Max cost:", min_value=0.0, value=1000.0, key="cost_max")
        
        with col2:
            st.subheader("Advanced Criteria")
            use_nested = st.checkbox("Use nested AND/OR logic", key="use_nested")
            
            if use_nested:
                nested_category = st.selectbox("Nested category:", 
                                             options=["", "Accommodation", "Shopping", "Culture"],
                                             key="nested_category")
                logic_operator = st.radio("Logic operator:", ["AND", "OR"], key="logic_op")
        
        if st.button("🔍 Recursive Search", key="recursive_search_btn"):
            # Build search criteria
            criteria = {}
            
            if search_category:
                criteria["category"] = search_category
            if search_location:
                criteria["location"] = search_location
            if cost_min < cost_max:
                criteria["cost_range"] = (cost_min, cost_max)
            
            # Add nested criteria if specified
            if use_nested and nested_category:
                nested_logic = logic_operator.lower()
                criteria[nested_logic] = {"category": nested_category}
            
            if criteria:
                with st.spinner("Performing recursive search..."):
                    results = recursive_timeline_search(st.session_state.timeline.items, criteria)
                
                st.subheader(f"🎯 Search Results ({len(results)} items found)")
                
                if results:
                    for item in results:
                        with st.container():
                            col1, col2, col3 = st.columns([2, 1, 1])
                            with col1:
                                st.markdown(f"**{item.title}**")
                                st.caption(f"{item.description}")
                            with col2:
                                st.text(f"📅 {item.date}")
                                st.text(f"📍 {item.location}")
                            with col3:
                                st.metric("Cost", f"${item.cost:.2f}")
                                st.text(f"🏷️ {item.category}")
                            st.markdown("---")
                else:
                    st.info("No items match the specified criteria. Try adjusting your search parameters.")
            else:
                st.warning("Please specify at least one search criterion.")
    
    # Educational section on recursion
    with st.expander("📚 Understanding Recursion in Budget Planning", expanded=False):
        st.markdown("""
        ### 🧮 Recursion Concepts Demonstrated
        
        **1. Hierarchical Budget Tree Creation**
        ```python
        def create_hierarchical_budget_tree(timeline, rules):
            # Base case: No items to process
            if not timeline.items:
                return empty_node
            
            # Recursive case: Create subcategories
            for category in categories:
                child_node = create_budget_subcategories(items, budget)
                # Recursion happens in create_budget_subcategories()
        ```
        
        **2. Recursive Optimization Analysis**
        ```python
        def recursive_budget_optimization(node, factor, depth):
            # Base case: Max depth or no children
            if depth > 5 or not node.children:
                return analysis_results
            
            # Recursive case: Analyze each child
            for child in node.children:
                child_analysis = recursive_budget_optimization(child, factor, depth + 1)
                # Process child results...
        ```
        
        **3. Recursive Search with Nested Criteria**
        ```python
        def recursive_timeline_search(items, criteria, depth):
            # Base case: No items or max depth
            if not items or depth > 3:
                return items
            
            # Recursive case: Apply nested criteria
            if has_nested_criteria:
                return recursive_timeline_search(filtered_items, nested_criteria, depth + 1)
        ```
        
        ### 🎯 Key Recursion Principles Applied
        - **Base Cases**: Clear stopping conditions (empty lists, max depth, single items)
        - **Recursive Cases**: Self-referential calls with modified parameters
        - **State Reduction**: Each recursive call works with smaller or simpler data
        - **Result Aggregation**: Combining results from recursive calls
        - **Depth Control**: Preventing infinite recursion with depth limits
        
        ### 💡 Real-World Applications
        - **Financial Planning**: Multi-level budget hierarchies
        - **Project Management**: Task breakdown structures  
        - **Data Analysis**: Hierarchical data exploration
        - **Optimization**: Iterative improvement algorithms
        """)

# --- Footer ---
st.markdown("---")

# --- Set Operations Demo Section ---
st.header("🧮 Python Set Operations Demo", divider="blue")
st.caption("Demonstrating set operations using travel destination domains")

# Create an expander for the set operations demo
with st.expander("🔍 Click to explore Set Operations in Budget Planning", expanded=False):
    st.markdown("""
    This section demonstrates Python set operations using three different categories of travel destinations:
    - **Set A**: Popular tourist destinations
    - **Set B**: Budget-friendly destinations  
    - **Set C**: Adventure travel destinations
    """)
    
    # Get the domain sets
    set_a, set_b, set_c = get_domain_sets()
    
    # Display the sets
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("🌟 Set A: Popular Destinations")
        st.write(set_a)
    
    with col2:
        st.subheader("💰 Set B: Budget-Friendly")
        st.write(set_b)
    
    with col3:
        st.subheader("🏔️ Set C: Adventure Destinations")
        st.write(set_c)
    
    # Button to perform operations
    if st.button("🔄 Perform All Set Operations", key="set_operations_btn"):
        results = perform_set_operations(set_a, set_b, set_c)
        
        st.markdown("### 📊 Set Operations Results")
        
        # 1. Union Operation
        st.markdown("#### 1. 🔗 Union Operation")
        st.markdown("**All unique destinations from all three sets:**")
        st.success(f"**Result:** {sorted(results['union'])}")
        st.code("union_result = set_a.union(set_b).union(set_c)")
        
        # 2. Intersection Operation
        st.markdown("#### 2. 🎯 Intersection Operation")
        st.markdown("**Destinations common to all three sets:**")
        if results['intersection']:
            st.success(f"**Result:** {sorted(results['intersection'])}")
        else:
            st.info("**Result:** No destinations are common to all three sets")
        st.code("intersection_result = set_a.intersection(set_b).intersection(set_c)")
        
        # 3. Difference Operations
        st.markdown("#### 3. ➖ Difference Operations")
        
        st.markdown("**a) Popular destinations that are NOT budget-friendly:**")
        if results['difference_a_b']:
            st.warning(f"**Result:** {sorted(results['difference_a_b'])}")
        else:
            st.info("**Result:** All popular destinations are budget-friendly")
        st.code("difference_a_b = set_a.difference(set_b)")
        
        st.markdown("**b) Adventure destinations that are NOT popular:**")
        if results['difference_c_a']:
            st.warning(f"**Result:** {sorted(results['difference_c_a'])}")
        else:
            st.info("**Result:** All adventure destinations are also popular")
        st.code("difference_c_a = set_c.difference(set_a)")
        
        # 4. Symmetric Difference Operation
        st.markdown("#### 4. ⚡ Symmetric Difference Operation")
        st.markdown("**Destinations that are either popular OR budget-friendly, but NOT both:**")
        if results['symmetric_diff_a_b']:
            st.info(f"**Result:** {sorted(results['symmetric_diff_a_b'])}")
        else:
            st.success("**Result:** No destinations are exclusively in one category")
        st.code("symmetric_diff_a_b = set_a.symmetric_difference(set_b)")
        
        # 5. Subset and Superset Operations
        st.markdown("#### 5. 🎯 Subset and Superset Operations")
        
        st.markdown("**a) Are all budget-friendly destinations also popular?**")
        if results['is_subset_b_a']:
            st.success("**Result:** ✅ YES - Budget-friendly destinations are a subset of popular destinations")
        else:
            st.error("**Result:** ❌ NO - Some budget-friendly destinations are not popular")
        st.code("is_subset_b_a = set_b.issubset(set_a)")
        
        st.markdown("**b) Do popular destinations include all adventure destinations?**")
        if results['is_superset_a_c']:
            st.success("**Result:** ✅ YES - Popular destinations include all adventure destinations")
        else:
            st.error("**Result:** ❌ NO - Popular destinations don't include all adventure destinations")
        st.code("is_superset_a_c = set_a.issuperset(set_c)")
        
        # Summary statistics using dictionary comprehension for metric definitions
        st.markdown("#### 📈 Summary Statistics")
        col1, col2, col3, col4 = st.columns(4)
        
        # Define metrics using dictionary comprehension
        metrics = {
            "Total Unique Destinations": len(results['union']),
            "Common to All Sets": len(results['intersection']),
            "Only Popular or Budget": len(results['symmetric_diff_a_b']),
            "Exclusive Adventure": len(results['difference_c_a'])
        }
        
        # Display metrics using list comprehension with column assignment
        columns = [col1, col2, col3, col4]
        [col.metric(label, value) for col, (label, value) in zip(columns, metrics.items())]
    
    # Educational section
    st.markdown("### 📚 Educational Notes")
    st.info("""
    **Set Operations Applications in Budget Planning:**
    - **Union**: Find all possible destinations to consider
    - **Intersection**: Identify destinations that meet multiple criteria
    - **Difference**: Discover unique characteristics of each category
    - **Symmetric Difference**: Find destinations that are exclusively in one category
    - **Subset/Superset**: Understand relationships between destination categories
    """)
    
    # Interactive section for custom sets
    st.markdown("### 🎮 Try Your Own Sets!")
    st.markdown("Enter your own sets of budget categories, activities, or destinations:")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        custom_set_a = st.text_area(
            "Enter Set A items (one per line):",
            value="Food\nTransport\nAccommodation\nEntertainment",
            key="custom_set_a",
            height=100
        )
    
    with col2:
        custom_set_b = st.text_area(
            "Enter Set B items (one per line):",
            value="Transport\nShopping\nAccommodation\nInsurance",
            key="custom_set_b",
            height=100
        )
    
    with col3:
        custom_set_c = st.text_area(
            "Enter Set C items (one per line):",
            value="Accommodation\nFood\nTours\nSouvenirs",
            key="custom_set_c",
            height=100
        )
    
    if st.button("🔄 Analyze Custom Sets", key="custom_sets_btn"):
        # Convert text input to sets using set comprehensions
        try:
            custom_a = {item.strip() for item in custom_set_a.split('\n') if item.strip()}
            custom_b = {item.strip() for item in custom_set_b.split('\n') if item.strip()}
            custom_c = {item.strip() for item in custom_set_c.split('\n') if item.strip()}
            
            if custom_a and custom_b and custom_c:
                custom_results = perform_set_operations(custom_a, custom_b, custom_c)
                
                st.markdown("#### 🎯 Your Custom Sets Analysis")
                
                # Using dictionary comprehension for result formatting
                result_labels = {
                    'union': "Union (All items):",
                    'intersection': "Intersection (Common items):",
                    'difference_a_b': "Set A - Set B:",
                    'difference_c_a': "Set C - Set A:",
                    'symmetric_diff_a_b': "Symmetric Difference (A ⊕ B):"
                }
                
                # Display set operation results using comprehension
                for key, label in result_labels.items():
                    result = custom_results[key]
                    display_value = sorted(result) if result else "None"
                    st.write(f"**{label}**", display_value)
                
                # Boolean results using dictionary comprehension
                boolean_results = {
                    'is_subset_b_a': "Is B ⊆ A?",
                    'is_superset_a_c': "Is A ⊇ C?"
                }
                
                for key, question in boolean_results.items():
                    answer = "✅ Yes" if custom_results[key] else "❌ No"
                    st.write(f"**{question}**", answer)
            else:
                st.warning("Please ensure all three sets have at least one item each.")
        except Exception as e:
            st.error(f"Error processing custom sets: {e}")

st.markdown("---")