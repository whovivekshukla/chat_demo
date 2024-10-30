from fastapi import FastAPI
from pydantic import BaseModel
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from typing import List
import requests

app = FastAPI()

class ChatMessage(BaseModel):
    content: str

# Load and prepare documents
file_path = "./test.pdf"
loader = PyPDFLoader(file_path)
pages = list(loader.load())

# Initialize components
vector_store = InMemoryVectorStore.from_documents(pages, OpenAIEmbeddings())
llm = ChatOpenAI(model="gpt-3.5-turbo")

# Create prompt template
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant answering questions about the LayoutParser paper Do not answer anything that is not present in this file No matter what. Use the following context to answer the question: {context}"),
    ("human", "{question}")
])

# Create chain
chain = prompt | llm | StrOutputParser()

@app.post("/api/chat/{session_id}")
async def chat(session_id: str, message: ChatMessage):
    # Get relevant documents
    relevant_docs = vector_store.similarity_search(message.content, k=2)
    context = "\n\n".join(doc.page_content for doc in relevant_docs)
    
    # Generate response using LLM
    response = chain.invoke({
        "context": context,
        "question": message.content
    })
    
    # Send the response to webhook
    webhook_payload = {
        "senderId": 5320,
        "receiverExternalId": 'a8ac5d00-3f77-4e59-9550-2cdae5c89e31',
        "message": response
    }
    
    webhook_url = "http://localhost:3000/api/webhook/ai-chatbot/listen/"
    headers = {
        "Content-Type": "application/json",
        "organization_code": "dev-demoorg",
        "api_key": "a29a99ac-383e-4ee9-bd76-3921b67b4c0c"
    }
    webhook_response = requests.post(webhook_url, json=webhook_payload, headers=headers)
    webhook_response.raise_for_status()
    
    return {"message": response}