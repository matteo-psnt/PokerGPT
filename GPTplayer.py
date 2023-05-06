from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.utilities import GoogleSerperAPIWrapper
from langchain.agents import initialize_agent, Tool, AgentType, load_tools
from langchain.schema import (
    AIMessage,
    HumanMessage,
    BaseMessage
)
from langchain.chains import ConversationChain
from settings import API_KEY
from poker import *
import os

llm = OpenAI()
search = GoogleSerperAPIWrapper()
tools = load_tools(["serpapi", "llm-math"], llm=llm)

self_ask_with_search = initialize_agent(tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True)



if __name__ == "__main__":
    i = self_ask_with_search.run("What is the hometown of the reigning men's U.S. Open champion?")
    print(i)
