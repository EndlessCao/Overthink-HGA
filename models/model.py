from typing import List, Sequence
from openai import OpenAI, AsyncOpenAI
from dotenv import load_dotenv
import os
from prompts.prompts import *
import json
import asyncio
import re
from abc import ABC, abstractmethod
load_dotenv()
TARGET_BASE_URL = os.getenv("TARGET_BASE_URL")
TARGET_API_KEY = os.getenv("TARGET_API_KEY")

ATTACKER_BASE_URL = os.getenv("ATTACKER_BASE_URL")
ATTACKER_API_KEY = os.getenv("ATTACKER_API_KEY")

class BaseProblem(ABC):
    def __init__(self, children: List[str], question: str|None = None):
        self.children = children.copy() if children is not None else []
        self.question = question
        self.fitness = 0.0
    
    @abstractmethod
    def to_prompt(self) -> str:
        ...
    
    @abstractmethod
    def __str__(self) -> str:
        ...
    
    def copy(self):
        new_problem = self.__class__(self.children.copy(), self.question)
        new_problem.fitness = self.fitness  
        return new_problem
    

class MathProblem(BaseProblem):
    
    def __init__(self, children: List[str], question: str):
        super().__init__(children=children, question=question)
        
    def to_prompt(self) -> str:
        if self.children:
            premises_text = ", ".join(self.children)
            return f"{premises_text}, {self.question}"
        else:
            return f"{self.question}"
    
    def __str__(self):
        return f"Premises: {self.children}, Question: {self.question}, Fitness: {self.fitness}\n Prompt: {self.to_prompt()}"

class Problem(BaseProblem):
    
    def __init__(self, children: List[str], question: str):
        super().__init__(children=children, question=question)
        
    def to_prompt(self) -> str:
        """Convert structured problem to full text prompt"""
        children_text = ", ".join(self.children)
        return f"{children_text}"
    
    def __str__(self):
        return f" Question:{self.children}, Fitness: {self.fitness}"


class TargetModel:
    def __init__(self, model_name):
        self.model_name = model_name
        self.client = OpenAI(api_key=TARGET_API_KEY, base_url=TARGET_BASE_URL)
        self.async_client = AsyncOpenAI(api_key=TARGET_API_KEY, base_url=TARGET_BASE_URL)

    def generate(self, prompt):
        completion = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
        )
        chat_usage = None
        if hasattr(completion, "usage") and completion.usage is not None:
            chat_usage = completion.usage
        content = completion.choices[0].message.model_extra.get('reasoning_content', completion.choices[0].message.content)
        return content, chat_usage
    def agenerate(self, prompts: List[str], n_samples=1):
        async def _agenerate(prompt):
            tasks = [
                self.async_client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                stream=False,
             ) for _ in range(n_samples)
            ]
            completions = await asyncio.gather(*tasks)
            contents = [completion.choices[0].message.model_extra.get('reasoning_content', completion.choices[0].message.content)\
                for completion in completions]
            chat_usages = [completions[i].usage for i in range(n_samples) if hasattr(completions[i], "usage") and completions[i].usage is not None]
            return contents, chat_usages if len(chat_usages) > 0 else None
        async def run():
            tasks = [_agenerate(prompt) for prompt in prompts]
            results = await asyncio.gather(*tasks)
            return results
        return asyncio.run(run())
    

class AttackerModel:
    def __init__(self, model_name, version="v2", number=3):
        self.model_name = model_name
        self.client = OpenAI(api_key=ATTACKER_API_KEY, base_url=ATTACKER_BASE_URL)
        self.async_client = AsyncOpenAI(api_key=ATTACKER_API_KEY, base_url=ATTACKER_BASE_URL)
        self.template = SPLIT_QUESTION_v2.format(number=number) if version == "v2" else SPLIT_QUESTION_v1
        self.version = version

    async def _agenerate(self, prompt) -> str:

        completion = await self.async_client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
        )
        return completion.choices[0].message.content # type: ignore

    def split_question(self, questions: List[str]) -> Sequence[BaseProblem]:
        async def run():
            tasks = [self._asplit_question(q) for q in questions]
            results = await asyncio.gather(*tasks)
            return results
        return asyncio.run(run()) 

    async def _asplit_question(self, question):
        prompt = self.template.format(question=question)
        response :str = await self._agenerate(prompt)
        clean_text = re.sub(r"^```json|```$", "", response.strip(), flags=re.MULTILINE).strip()
        res = json.loads(clean_text)
        print(res)
        if self.version == "v2":
            data = {"children": res["sub_question"], "question": question}
            return Problem(**data)
        else:
            data = {"children": res["premises"], "question": res["question"]}
            return MathProblem(**data)

    
    

    
    
    