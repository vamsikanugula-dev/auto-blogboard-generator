from typing import Optional, List

from langchain_groq import ChatGroq
from langchain_core.tools import BaseTool
from langgraph.prebuilt import create_react_agent

from blogboard.config.settings import app_settings
from blogboard.tools import TavilySearchTool, GuardianSearchTool


class LLMAgentService:
    """
    Central LLM service used by BlogBoard agents.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
    ):
        self.model_name = (
            model_name
            or app_settings.llm.MODEL_NAME
        )

        self.temperature = (
            temperature
            if temperature is not None
            else app_settings.llm.TEMPERATURE
        )

        self.api_key = app_settings.llm.API_KEY

        self.llm = self._initialize_llm()

    def _initialize_llm(self) -> ChatGroq:
        return ChatGroq(
            model=self.model_name,
            temperature=self.temperature,
            api_key=self.api_key,
            max_tokens=2000,
             max_retries=5,  
        )

    # ---------------------------------------------------------
    # News Agent
    # ---------------------------------------------------------

    def get_news_agent(
        self,
        system_prompt: Optional[str] = None,
    ):
        """
        Create the News Research ReAct agent.

        Current LangGraph versions use `prompt` for the
        system instruction.
        """

        news_tools: List[BaseTool] = [
            TavilySearchTool(),
            GuardianSearchTool(),
        ]

        agent = create_react_agent(
            model=self.llm,
            tools=news_tools,
            prompt=system_prompt,
        )

        return agent

    # ---------------------------------------------------------
    # Custom Agent
    # ---------------------------------------------------------

    def get_custom_agent(
        self,
        tools: List[BaseTool],
        system_prompt: Optional[str] = None,
    ):
        """
        Create a generic ReAct agent with arbitrary tools.
        """

        agent = create_react_agent(
            model=self.llm,
            tools=tools,
            prompt=system_prompt,
        )

        return agent