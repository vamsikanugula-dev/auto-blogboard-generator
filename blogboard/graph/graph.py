from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

from blogboard.graph.state import BlogState

from blogboard.agents.tutorial_agent.agent import tutorial_node
from blogboard.agents.news_agent.agent import news_node
from blogboard.agents.validator_agent.agent import validator_node


# =========================================================
# ROUTING: AFTER NEWS VALIDATOR
# =========================================================

def _route_after_news_validator(state: BlogState) -> str:
    """
    Route after validating the AI News article.

    REJECTED:
        News Validator -> News Agent
        The News Agent revises the existing news article.

    APPROVED:
        News Validator -> Tutorial Agent
        The approved news context is passed to the Tutorial Agent.
    """

    if state.get("revision_needed", False):
        print(
            "  [GRAPH] News article rejected "
            "-> News Agent revision"
        )
        return "news_agent"

    print(
        "  [GRAPH] News article approved "
        "-> Tutorial Agent"
    )

    return "tutorial_agent"


# =========================================================
# ROUTING: AFTER TUTORIAL VALIDATOR
# =========================================================

def _route_after_tutorial_validator(state: BlogState) -> str:
    """
    Route after validating the Tutorial article.

    REJECTED:
        Tutorial Validator -> Tutorial Agent

    APPROVED:
        Tutorial Validator -> END
    """

    if state.get("revision_needed", False):
        print(
            "  [GRAPH] Tutorial article rejected "
            "-> Tutorial Agent revision"
        )
        return "tutorial_agent"

    print(
        "  [GRAPH] Tutorial article approved "
        "-> Pipeline complete"
    )

    return END


# =========================================================
# BUILD GRAPH
# =========================================================

def build_graph() -> StateGraph:
    """
    Build the BlogBoard daily generation pipeline.

    Pipeline:

        START
          |
          v
       News Agent
          |
          v
      News Validator
        /     \
   reject     approve
     |           |
     v           v
   News       Tutorial
   Agent       Agent
                 |
                 v
          Tutorial Validator
             /       \
        reject       approve
          |             |
          v             v
       Tutorial        END
        Agent


    The Tutorial Agent receives the news context generated
    by the News Agent and:

    1. Determines the most relevant tutorial domain.
    2. If no suitable domain exists, randomly selects one
       from the supported tutorial domains.
    3. Generates a tutorial topic related to the news.
    4. Generates the tutorial article.
    5. Preserves the selected domain/topic during revisions.

    article_type is maintained in BlogState:

        "ainews"   -> News article
        "tutorial" -> Tutorial article
    """

    builder = StateGraph(BlogState)

    # =====================================================
    # 1. REGISTER NODES
    # =====================================================

    builder.add_node(
        "news_agent",
        news_node
    )

    builder.add_node(
        "news_validator",
        validator_node
    )

    builder.add_node(
        "tutorial_agent",
        tutorial_node
    )

    builder.add_node(
        "tutorial_validator",
        validator_node
    )

    # =====================================================
    # 2. START -> NEWS AGENT
    # =====================================================

    builder.add_edge(
        START,
        "news_agent"
    )

    # =====================================================
    # 3. NEWS AGENT -> NEWS VALIDATOR
    # =====================================================

    builder.add_edge(
        "news_agent",
        "news_validator"
    )

    # =====================================================
    # 4. NEWS VALIDATOR ROUTING
    #
    # APPROVED:
    #       -> Tutorial Agent
    #
    # REJECTED:
    #       -> News Agent
    # =====================================================

    builder.add_conditional_edges(
        "news_validator",
        _route_after_news_validator,
        {
            "news_agent": "news_agent",
            "tutorial_agent": "tutorial_agent",
        }
    )

    # =====================================================
    # 5. TUTORIAL AGENT -> TUTORIAL VALIDATOR
    # =====================================================

    builder.add_edge(
        "tutorial_agent",
        "tutorial_validator"
    )

    # =====================================================
    # 6. TUTORIAL VALIDATOR ROUTING
    #
    # APPROVED:
    #       -> END
    #
    # REJECTED:
    #       -> Tutorial Agent
    # =====================================================

    builder.add_conditional_edges(
        "tutorial_validator",
        _route_after_tutorial_validator,
        {
            "tutorial_agent": "tutorial_agent",
            END: END,
        }
    )

    # =====================================================
    # 7. COMPILE
    # =====================================================

    return builder.compile(
        checkpointer=InMemorySaver()
    )


# =========================================================
# EXPOSE COMPILED GRAPH
# =========================================================

graph = build_graph()

	