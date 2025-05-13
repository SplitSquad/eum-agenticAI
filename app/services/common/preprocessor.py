# app/services/common/preprocessor.py
from langchain_groq import ChatGroq
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
import json
# 기존: from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from app.core.llm_client import get_langchain_llm

def translate_query(query) : 
    llm = get_langchain_llm(is_lightweight=False)


    parser = JsonOutputParser(pydantic_object={
        "type": "object",
        "properties": {
            "lang_code": {"type": "string"},
            "translated_query": {"type": "string"}
        }
    })


    translation = """
    ---------------------------------------------------------------------------------------------------------
    input : 인공지능은 사람처럼 학습하고 문제를 해결할 수 있습니다.
    lang_code : ko
    translated_query : Artificial intelligence can learn and solve problems like humans.
    keyword : artificial intelligence, like humans, learning, problem solving
    intention : Provide information (Explain a technical concept)

    input : 날씨가 점점 더워지고 있어요.
    lang_code : ko
    translated_query : The weather is getting hotter.
    keyword : weather, heat, change
    intention : Express state (Share a daily observation)

    input : 이 책은 과학에 대한 흥미로운 이야기를 담고 있습니다.
    lang_code : ko
    translated_query : This book contains fascinating stories about science.
    keyword : book, science, story, fascinating
    intention : Provide information (Introduce a book or content)
    ---------------------------------------------------------------------------------------------------------
    input : Artificial intelligence is transforming every industry.  
    lang_code : en  
    translated_query : Artificial intelligence is transforming every industry.  
    keyword : artificial intelligence, transformation, industry  
    intention : Provide information (Explain a technical concept)

    input : The weather is becoming increasingly unpredictable.  
    lang_code : en  
    translated_query : The weather is becoming increasingly unpredictable.  
    keyword : weather, unpredictability, change  
    intention : Express state (Describe environmental change)

    input : This book offers a detailed look at the history of science.  
    lang_code : en  
    translated_query : This book offers a detailed look at the history of science.  
    keyword : book, science, history, detailed look  
    intention : Provide information (Introduce a book or content)
    ---------------------------------------------------------------------------------------------------------
    input : 人工知能はあらゆる産業を変革しています。  
    lang_code : ja  
    translated_query : Artificial intelligence is transforming every industry.  
    keyword : artificial intelligence, industry, transformation  
    intention : Provide information (Explain a technical concept)

    input : 天気がますます予測できなくなっています。  
    lang_code : ja  
    translated_query : The weather is becoming increasingly unpredictable.  
    keyword : weather, unpredictability, climate change  
    intention : Express state (Describe environmental change)

    input : この本は科学の歴史について詳しく説明しています。  
    lang_code : ja  
    translated_query : This book offers a detailed look at the history of science.  
    keyword : book, science, history, explanation  
    intention : Provide information (Introduce a book or content)
    ---------------------------------------------------------------------------------------------------------
    input : 人工智能正在改变各行各业。  
    lang_code : zh  
    translated_query : Artificial intelligence is transforming every industry.  
    keyword : artificial intelligence, industry, transformation  
    intention : Provide information (Explain a technical concept)

    input : 天气变得越来越难以预测。  
    lang_code : zh  
    translated_query : The weather is becoming increasingly unpredictable.  
    keyword : weather, unpredictability, climate change  
    intention : Express state (Describe environmental change)

    input : 这本书详细介绍了科学史。  
    lang_code : zh  
    translated_query : This book offers a detailed look at the history of science.  
    keyword : book, history of science, introduction, detailed content  
    intention : Provide information (Introduce a book or content)
    ---------------------------------------------------------------------------------------------------------
    input : La inteligencia artificial está transformando todas las industrias.  
    lang_code : es  
    translated_query : Artificial intelligence is transforming every industry.  
    keyword : artificial intelligence, industry, transformation  
    intention : Provide information (Explain a technical concept)

    input : El clima se está volviendo cada vez más impredecible.  
    lang_code : es  
    translated_query : The weather is becoming increasingly unpredictable.  
    keyword : weather, unpredictability, climate change  
    intention : Express state (Describe environmental change)

    input : Este libro ofrece una mirada detallada a la historia de la ciencia.  
    lang_code : es  
    translated_query : This book offers a detailed look at the history of science.  
    keyword : book, history of science, detailed view  
    intention : Provide information (Introduce a book or content)
    ---------------------------------------------------------------------------------------------------------
    input : L'intelligence artificielle transforme toutes les industries.  
    lang_code : fr  
    translated_query : Artificial intelligence is transforming every industry.  
    keyword : artificial intelligence, industry, transformation  
    intention : Provide information (Explain a technical concept)

    input : Le temps devient de plus en plus imprévisible.  
    lang_code : fr  
    translated_query : The weather is becoming increasingly unpredictable.  
    keyword : weather, unpredictability, climate change  
    intention : Express state (Describe environmental change)

    input : Ce livre propose un regard détaillé sur l'histoire des sciences.  
    lang_code : fr  
    translated_query : This book offers a detailed look at the history of science.  
    keyword : book, history of science, detailed view  
    intention : Provide information (Introduce a book or content)
    ---------------------------------------------------------------------------------------------------------
    input : Künstliche Intelligenz verändert jede Branche.  
    lang_code : de  
    translated_query : Artificial intelligence is transforming every industry.  
    keyword : artificial intelligence, industry, transformation  
    intention : Provide information (Explain a technical concept)

    input : Das Wetter wird immer unvorhersehbarer.  
    lang_code : de  
    translated_query : The weather is becoming increasingly unpredictable.  
    keyword : weather, unpredictability, climate change  
    intention : Express state (Describe environmental change)

    input : Dieses Buch bietet einen detaillierten Einblick in die Wissenschaftsgeschichte.  
    lang_code : de  
    translated_query : This book offers a detailed look at the history of science.  
    keyword : book, history of science, detailed insight  
    intention : Provide information (Introduce a book or content)
    ---------------------------------------------------------------------------------------------------------
    input : Искусственный интеллект трансформирует все отрасли.  
    lang_code : ru  
    translated_query : Artificial intelligence is transforming every industry.  
    keyword : artificial intelligence, industry, transformation  
    intention : Provide information (Explain a technical concept)

    input : Погода становится все менее предсказуемой.  
    lang_code : ru  
    translated_query : The weather is becoming increasingly unpredictable.  
    keyword : weather, unpredictability, climate change  
    intention : Express state (Describe environmental change)

    input : Эта книга предлагает подробный взгляд на историю науки.  
    lang_code : ru  
    translated_query : This book offers a detailed look at the history of science.  
    keyword : book, history of science, detailed view  
    intention : Provide information (Introduce a book or content)
    ---------------------------------------------------------------------------------------------------------


    """

    # 프롬프트 문자열 구성
    system_prompt_template = f"""
    1. This is the part that analyzes language.
    2. Please tell me which language it is
    3. Please translate it into English
    4. few-shot example 
    {translation}


    ⚠️ Do NOT include any explanation or message. ONLY return a valid JSON object. No natural language.
    """

    # print("[TRANSTRATE SYSTEM PROMPT] ",system_prompt_template)

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt_template ),
        ("user", "{input}")
    ])

    chain = prompt | llm | parser

    def parse_product(description: str) -> dict:
        result = chain.invoke({"input": description})
        return result

    description = query

    response = parse_product(description)
    print("[TRANSTRATE OUTPUT] ",response)

    return response


