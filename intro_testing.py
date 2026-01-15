from dotenv import load_dotenv
import os
from langgraph.graph import Graph
from langchain_groq import ChatGroq 
from IPython.display import Image, display

load_dotenv()  # This loads the .env file

'''llm = ChatGroq(model="meta-llama/llama-4-scout-17b-16e-instruct")
print(llm.invoke("How do i get rid of pimples tell me steps?").content)''' #if we use without .content it will give us whole response in json includinh \n

def function1(input):
    llm= ChatGroq(model="meta-llama/llama-4-scout-17b-16e-instruct")
    response = llm.invoke("hi how are you?").content
    return response
print(function1("hi how are you?"))

def function2(input):
    upper_string=input.upper()
    return upper_string
print(function2("hello world")) #output: HELLO WORLD

workflow = Graph()
workflow.add_node("function1", function1)
workflow.add_node("function2", function2)
workflow.add_edge("function1","function2") #how nodes are connected to each other what we are passing from one node to another
workflow.set_entry_point("function1")  #set entry point for the workflow
workflow.set_finish_point("function2")  #set exit point for the workflow
app=workflow.compile()
# Get the PNG image bytes
image_bytes = app.get_graph().draw_mermaid_png()

# Save the image as a PNG file
with open("workflow_graph.png", "wb") as f:
    f.write(image_bytes)

print("Graph saved as workflow_graph.png")





