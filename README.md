Template for creating and submitting MAT496 capstone project.

# Overview of MAT496

In this course, we have primarily learned Langgraph. This is helpful tool to build apps which can process unstructured `text`, find information we are looking for, and present the format we choose. Some specific topics we have covered are:

- Prompting
- Structured Output 
- Semantic Search
- Retreaval Augmented Generation (RAG)
- Tool calling LLMs & MCP
- Langgraph: State, Nodes, Graph

We also learned that Langsmith is a nice tool for debugging Langgraph codes.

------

# Capstone Project objective

The first purpose of the capstone project is to give a chance to revise all the major above listed topics. The second purpose of the capstone is to show your creativity. Think about all the problems which you can not have solved earlier, but are not possible to solve with the concepts learned in this course. For example, We can use LLM to analyse all kinds of news: sports news, financial news, political news. Another example, we can use LLMs to build a legal assistant. Pretty much anything which requires lots of reading, can be outsourced to LLMs. Let your imagination run free.


-------------------------

# Project report Template

## Title: Personal Agent 

## Overview
# Personal AI Agent – Project Overview

This project is a personal AI agent built to help with everyday tasks in a natural, intuitive way. It can assist with assignments, remember important dates like birthdays, gather your feedback, provide simple information such as weather updates, and generally act as a reliable companion that understands and adapts to your needs.

The focus of the project is to create an assistant that feels genuinely helpful, continues to improve over time, and supports the user in a practical, meaningful way.

---

## How the Agent Works

The agent processes user queries using a combination of methods rather than relying on a single approach. This layered system allows it to produce responses that are accurate, relevant, and grounded.

### Retrieval-Augmented Generation (RAG)  
RAG is used to pull in relevant information from previously stored documents or indexed data. This ensures the model provides responses based on real context instead of relying solely on generative predictions.

### Semantic Search  
Semantic search helps the agent find information based on meaning rather than keywords. This improves the relevance of the retrieved content, especially when user queries are vague or phrased differently from stored data.

### Tool Processing  
For tasks that require external actions, such as calculations or fetching weather information, the agent uses predefined tools. These tools allow the system to interact with data outside the model.

### LLM Reasoning  
When necessary, the agent uses direct language model reasoning to interpret the user’s request and generate an appropriate response.

All candidate responses produced through these methods are evaluated with the help of Evaluators to determine which is the most suitable. This ensures that the user receives the most accurate and contextually appropriate answer.

---

## Memory and Conversation Continuity

The agent maintains a threaded memory system that allows it to recall past conversations and important user details. Because of this, the user can return to a previous topic at any time and continue seamlessly.

This memory system also allows the agent to store and recall personal information such as birthdays, preferences, and tasks, making the interaction more personalized.

---

## Advanced Reasoning Features

To handle complex tasks effectively, the agent incorporates several additional reasoning structures.

### Reduction Logic  
If multiple components generate responses, the system merges them into a single coherent answer. This reduces confusion and improves clarity.

### Map-Reduce Patterns  
Large or complex problems are broken down into smaller segments, processed individually, and then combined into a final response. This helps the agent deal with multi-step or detailed tasks.

### Refinement Loop  
If the user indicates that an answer is unclear or incorrect, the agent reprocesses the query and improves the response. This creates a natural feedback loop that helps the system evolve.

### ReAct-Style Reasoning  
The agent uses a blend of reasoning and action steps, allowing it to think through a problem and trigger tools when necessary. This structure supports multi-step reasoning similar to how real agents operate.

---

## Continuous Learning with LangSmith

All user interactions are stored as LangSmith datasets. These datasets serve as training material and allow the system to be evaluated and improved over time. This creates a human-in-the-loop learning environment where user feedback directly contributes to the growth of the model.

---

## Reason for picking up this project

The reason for choosing this project is that personal agents are typically built on top of LLMs, which provide the intelligence needed to understand instructions, maintain context, and generate useful responses. After completing an LLM course, creating a personal agent is the most practical way to apply and reinforce every concept learned. This project also helps deepen understanding of how widely used models like ChatGPT, Claude, and Groq operate. Additionally, it provides hands-on experience with features such as memory, tool usage, and the processes involved in training or customizing models. For these reasons, building a Personal Assistant is the most suitable and meaningful project I could undertake after completing the LLM course.

## Video Summary Link: 

Make a short -  3-5 min video of yourself, put it on youtube/googledrive, and put its link in your README.md.

- you can use this free tool for recording https://screenrec.com/
- Video format should be like this:
- your face should be visible
- State the overall job of your agent: what inputs it takes, and what output it gives.
- Very quickly, explain how your agent acts on the input and spits out the output. 
- show an example run of the agent in the video


## Plan

I plan to execute these steps to complete my project.

- [TODO] Step 1: Create a proper project structure
- [TODO] Step 2: Create a `.env` file and add API keys
- [TODO] Step 3: Create a central configuration file
- [TODO] Step 4: Create the knowledge base and prepare learned queries
- [TODO] Step 5: Create tools (Base Tool, Weather Tool, Calculator Tool, Time Tool, Web-Search Tool)  
- [TODO] Step 6: Create the Tool Manager  
- [TODO] Step 7: Create the LLM client  
- [TODO] Step 8: Create the RAG system
- [TODO] Step 9: Creating Semantic Search Agent  
- [TODO] Step 10: Creating Evaluator  
- [TODO] Step 11: Creating ReAct-agent  
- [TODO] Step 12: Creating memory manager and extractor
- [TODO] Step 13: Creating main model (Personal Assistant)  
- [TODO] Step 14: Adding human-in-loop mechanism  
- [TODO] Step 15: Adding Assistant CLI  
- [TODO] Step 16: Adding langgraph
- [TODO] Step 17: Adding mermaid diagram of project workflow
- [TODO] Step 18: Adding requirements file 


## Conclusion:

I had planned to achieve {this this}. I think I have/have-not achieved the conclusion satisfactorily. The reason for your satisfaction/unsatisfaction.

----------

# Added instructions:

- This is a `solo assignment`. Each of you will work alone. You are free to talk, discuss with chatgpt, but you are responsible for what you submit. Some students may be called for viva. You should be able to each and every line of work submitted by you.

- `commit` History maintenance.
  - Fork this repository and build on top of that.
  - For every step in your plan, there has to be a commit.
  - Change [TODO] to [DONE] in the plan, before you commit after that step. 
  - The commit history should show decent amount of work spread into minimum two dates. 
  - **All the commits done in one day will be rejected**. Even if you are capable of doing the whole thing in one day, refine it in two days.  
 
 - Deadline: Dec 2nd, Tuesday 11:59 pm


# Grading: total 25 marks

- Coverage of most of topics in this class: 20
- Creativity: 5
  
