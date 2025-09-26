print("--- TESTING LANGCHAIN OLLAMA CONNECTION ---")
try:
    from langchain_community.chat_models import ChatOllama
    print("✅ Imported ChatOllama successfully.")

    print("\nInstantiating ChatOllama with model 'phi3:mini'...")
    # We'll set a timeout to prevent it from hanging forever
    llm = ChatOllama(model="phi3:mini", request_timeout=120.0) # type: ignore
    print("✅ Instantiated LLM object.")

    print("\nSending a simple prompt ('hello') to the model via .invoke()...")
    print("(This is the step that is currently hanging in the agent.)")
    
    # This is the simplest possible call to the model.
    response = llm.invoke("hello")

    print("\n--- RESPONSE ---")
    print(response)
    print("\n🎉 SUCCESS: LangChain can connect to and get a response from Ollama.")

except Exception as e:
    print("\n❌ FAILED: An error occurred during the connection test.")
    import traceback
    traceback.print_exc()