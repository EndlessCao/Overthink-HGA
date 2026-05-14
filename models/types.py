from abc import abstractmethod, ABC
from typing import List

class BaseProblem(ABC):
    def __init__(self, children: List[str], question: str|None = None):
        self.children = children.copy() if children is not None else []
        self.question = question
        self.fitness = 0.0

    @abstractmethod
    def to_prompt(self) -> str:
        pass

    @abstractmethod
    def __str__(self) -> str:
        pass

    def copy(self):
        new_problem = self.__class__(self.children.copy(), self.question)
        new_problem.fitness = self.fitness
        return new_problem

class MathProblem(BaseProblem):

    def __init__(self, premises: List[str], question: str):
        super().__init__(children=premises, question=question)

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