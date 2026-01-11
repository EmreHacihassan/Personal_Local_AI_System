"""
Calculator Tool
===============

Matematiksel hesaplamalar için güvenli araç.
"""

import ast
import math
import operator
from typing import Any, Dict, Union

from .base_tool import BaseTool


class CalculatorTool(BaseTool):
    """
    Güvenli matematiksel hesaplama aracı
    
    Desteklenen operasyonlar:
    - Aritmetik: +, -, *, /, //, %, **
    - Trigonometri: sin, cos, tan, asin, acos, atan
    - Logaritma: log, log10, log2, exp
    - Diğer: sqrt, abs, round, ceil, floor
    """
    
    name = "calculator"
    description = "Matematiksel hesaplamalar yapar. Örnek: '2 + 2', 'sqrt(16)', 'sin(3.14/2)'"
    
    # İzin verilen operatörler
    ALLOWED_OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }
    
    # İzin verilen fonksiyonlar
    ALLOWED_FUNCTIONS = {
        # Trigonometri
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "asin": math.asin,
        "acos": math.acos,
        "atan": math.atan,
        "sinh": math.sinh,
        "cosh": math.cosh,
        "tanh": math.tanh,
        
        # Logaritma
        "log": math.log,
        "log10": math.log10,
        "log2": math.log2,
        "exp": math.exp,
        
        # Kök ve üs
        "sqrt": math.sqrt,
        "pow": pow,
        
        # Yuvarlama
        "abs": abs,
        "round": round,
        "ceil": math.ceil,
        "floor": math.floor,
        
        # Diğer
        "factorial": math.factorial,
        "gcd": math.gcd,
        "degrees": math.degrees,
        "radians": math.radians,
    }
    
    # İzin verilen sabitler
    ALLOWED_CONSTANTS = {
        "pi": math.pi,
        "e": math.e,
        "tau": math.tau,
        "inf": math.inf,
    }
    
    def _safe_eval(self, node: ast.AST) -> Union[int, float]:
        """AST node'unu güvenli şekilde değerlendir"""
        if isinstance(node, ast.Num):  # Python 3.7
            return node.n
        
        elif isinstance(node, ast.Constant):  # Python 3.8+
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError(f"Desteklenmeyen sabit: {node.value}")
        
        elif isinstance(node, ast.BinOp):
            left = self._safe_eval(node.left)
            right = self._safe_eval(node.right)
            op_type = type(node.op)
            
            if op_type not in self.ALLOWED_OPERATORS:
                raise ValueError(f"Desteklenmeyen operatör: {op_type.__name__}")
            
            return self.ALLOWED_OPERATORS[op_type](left, right)
        
        elif isinstance(node, ast.UnaryOp):
            operand = self._safe_eval(node.operand)
            op_type = type(node.op)
            
            if op_type not in self.ALLOWED_OPERATORS:
                raise ValueError(f"Desteklenmeyen operatör: {op_type.__name__}")
            
            return self.ALLOWED_OPERATORS[op_type](operand)
        
        elif isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise ValueError("Sadece basit fonksiyon çağrıları destekleniyor")
            
            func_name = node.func.id
            
            if func_name not in self.ALLOWED_FUNCTIONS:
                raise ValueError(f"Desteklenmeyen fonksiyon: {func_name}")
            
            args = [self._safe_eval(arg) for arg in node.args]
            return self.ALLOWED_FUNCTIONS[func_name](*args)
        
        elif isinstance(node, ast.Name):
            if node.id in self.ALLOWED_CONSTANTS:
                return self.ALLOWED_CONSTANTS[node.id]
            raise ValueError(f"Desteklenmeyen değişken: {node.id}")
        
        elif isinstance(node, ast.Expression):
            return self._safe_eval(node.body)
        
        else:
            raise ValueError(f"Desteklenmeyen ifade tipi: {type(node).__name__}")
    
    async def _run(self, expression: str) -> Dict[str, Any]:
        """
        Matematiksel ifadeyi hesapla
        
        Args:
            expression: Matematiksel ifade (örn: "2 + 2", "sqrt(16)")
            
        Returns:
            Hesaplama sonucu
        """
        try:
            # Expression'ı parse et
            tree = ast.parse(expression, mode='eval')
            
            # Güvenli değerlendirme
            result = self._safe_eval(tree)
            
            return {
                "success": True,
                "expression": expression,
                "result": result,
                "type": type(result).__name__
            }
        
        except SyntaxError as e:
            return {
                "success": False,
                "expression": expression,
                "error": f"Sözdizimi hatası: {e}",
                "hint": "Geçerli bir matematiksel ifade girin"
            }
        
        except ValueError as e:
            return {
                "success": False,
                "expression": expression,
                "error": str(e)
            }
        
        except ZeroDivisionError:
            return {
                "success": False,
                "expression": expression,
                "error": "Sıfıra bölme hatası"
            }
        
        except Exception as e:
            return {
                "success": False,
                "expression": expression,
                "error": f"Hesaplama hatası: {str(e)}"
            }
    
    def get_schema(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Hesaplanacak matematiksel ifade"
                    }
                },
                "required": ["expression"]
            }
        }


# Tool instance
calculator_tool = CalculatorTool()
