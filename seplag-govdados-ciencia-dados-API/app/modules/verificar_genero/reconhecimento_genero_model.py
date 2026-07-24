# model.py
import os
import re
import joblib
from typing import Optional, Dict, Any, Tuple
from pathlib import Path
import numpy as np

class SexPredictor:
    """
    Espera um .pkl que é uma tupla: (model, vectorizer)
    - model: sklearn com .predict_proba e .classes_
    - vectorizer: sklearn com .transform
    """
    
    def __init__(self, model_path: str = None):

        model_path = os.getenv("MODEL_GENERO")
        #or os.getenv("MODEL_GENERO", "models/modelo_genero.pkl")
        p = Path(model_path)
        if not p.exists():
            raise FileNotFoundError(f"Modelo não encontrado: {p}")

        obj = joblib.load(p)
        if not isinstance(obj, tuple) or len(obj) < 2:
            raise TypeError("Esperado pickle como tupla (model, vectorizer).")

        self.model, self.vectorizer = obj[0], obj[1]

        # sanity checks
        for attr in ("predict_proba", "classes_"):
            if not hasattr(self.model, attr):
                raise TypeError(f"model precisa ter .{attr}")
        if not hasattr(self.vectorizer, "transform"):
            raise TypeError("vectorizer precisa ter .transform")

        # Índices das classes (garante que acharemos 'M','F','UNISSEX' se existirem)
        self.classes_: np.ndarray = np.array(self.model.classes_, dtype=object)

    @staticmethod
    def first_name(nome: Optional[str]) -> str:
        if not isinstance(nome, str) or not nome.strip():
            return ""
        fn = nome.strip().split()[0]
        return re.sub(r"[^A-Za-zÀ-ÿ'’-]", "", fn)

    def _proba_dict(self, nome: str) -> Dict[str, float]:
        """
        Retorna dict {classe: prob} usando predict_proba.
        """
        # teu treino usa Title Case:
        X = self.vectorizer.transform([nome.title()])
        probs = self.model.predict_proba(X)[0]  # array 1D
        return {str(cls).upper(): float(p) for cls, p in zip(self.classes_, probs)}

    def classify(self, first_name: str) -> str:
        """
        Retorna 'M' | 'F' | 'U'
        - Se a classe 'UNISSEX' existir e for a top-1, retorna 'U'
        - Caso contrário, retorna 'M' ou 'F' conforme top-1
        """
        if not first_name:
            return "U"

        proba = self._proba_dict(first_name)
        # pega a classe com maior prob
        top_cls = max(proba.items(), key=lambda kv: kv[1])[0]  # classe em UPPER
        if top_cls in ("U", "UNISSEX"):
            return "U"
        if top_cls in ("M", "MASCULINO"):
            return "M"
        if top_cls in ("F", "FEMININO"):
            return "F"
        # fallback: se não reconhecer, trata como U
        return "U"

    def classify_with_proba(self, first_name: str) -> Dict[str, Any]:
        """
        Retorna:
          {
            'sexo_predito': 'M'|'F'|'U',
            'prob_feminino': ...,
            'prob_masculino': ...,
            'prob_unissex': ...
          }
        """
        if not first_name:
            return {
                "sexo_predito": "U",
                "prob_feminino": 0.0,
                "prob_masculino": 0.0,
                "prob_unissex": 1.0
            }

        proba = self._proba_dict(first_name)  # classes upper
        prob_f = proba.get("F", 0.0) or proba.get("FEMININO", 0.0)
        prob_m = proba.get("M", 0.0) or proba.get("MASCULINO", 0.0)
        prob_u = proba.get("UNISSEX", 0.0)

        # decide o rótulo final
        if prob_u >= prob_f and prob_u >= prob_m:
            label = "U"
        elif prob_m >= prob_f:
            label = "M"
        else:
            label = "F"

        return {
            "sexo_predito": label,
            "prob_feminino": round(float(prob_f), 3),
            "prob_masculino": round(float(prob_m), 3),
            "prob_unissex": round(float(prob_u), 3),
        }
