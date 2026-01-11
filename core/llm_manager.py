"""
Enterprise AI Assistant - LLM Manager
Endüstri Standartlarında Kurumsal AI Çözümü

Ollama tabanlı LLM yönetimi - model seçimi, fallback ve streaming desteği.
"""

import asyncio
from typing import AsyncGenerator, Optional
import ollama
from tenacity import retry, stop_after_attempt, wait_exponential

from .config import settings


class LLMManager:
    """
    LLM yönetim sınıfı - Endüstri standartlarına uygun.
    
    Özellikler:
    - Primary/Backup model desteği
    - Automatic fallback
    - Streaming response
    - Retry mekanizması
    """
    
    def __init__(
        self,
        primary_model: Optional[str] = None,
        backup_model: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.primary_model = primary_model or settings.OLLAMA_PRIMARY_MODEL
        self.backup_model = backup_model or settings.OLLAMA_BACKUP_MODEL
        self.base_url = base_url or settings.OLLAMA_BASE_URL
        self.client = ollama.Client(host=self.base_url)
        self._current_model = self.primary_model
    
    def check_model_available(self, model_name: str) -> bool:
        """Model'in mevcut olup olmadığını kontrol et."""
        try:
            models = self.client.list()
            available_models = [m["name"] for m in models.get("models", [])]
            # Check for exact match or partial match (with tags)
            return any(
                model_name in m or m.startswith(model_name.split(":")[0])
                for m in available_models
            )
        except Exception:
            return False
    
    def pull_model(self, model_name: str) -> bool:
        """Model'i indir."""
        try:
            print(f"📥 Model indiriliyor: {model_name}")
            self.client.pull(model_name)
            print(f"✅ Model indirildi: {model_name}")
            return True
        except Exception as e:
            print(f"❌ Model indirilemedi: {e}")
            return False
    
    def ensure_model(self, model_name: str) -> bool:
        """Model'in mevcut olduğundan emin ol, yoksa indir."""
        if not self.check_model_available(model_name):
            return self.pull_model(model_name)
        return True
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """
        Senkron LLM yanıtı üret.
        
        Args:
            prompt: Kullanıcı prompt'u
            system_prompt: Sistem prompt'u (opsiyonel)
            temperature: Yaratıcılık seviyesi (0-1)
            max_tokens: Maksimum token sayısı
            
        Returns:
            LLM yanıtı
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = self.client.chat(
                model=self._current_model,
                messages=messages,
                options={
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            )
            return response["message"]["content"]
        except Exception as e:
            # Fallback to backup model
            if self._current_model != self.backup_model:
                print(f"⚠️ Primary model başarısız, backup deneniyor: {e}")
                self._current_model = self.backup_model
                return self.generate(prompt, system_prompt, temperature, max_tokens)
            raise
    
    async def generate_async(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """Asenkron LLM yanıtı üret."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.generate(prompt, system_prompt, temperature, max_tokens)
        )
    
    def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[str, None]:
        """
        Streaming LLM yanıtı üret.
        
        Yields:
            Token parçaları
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        try:
            stream = self.client.chat(
                model=self._current_model,
                messages=messages,
                options={
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
                stream=True,
            )
            
            for chunk in stream:
                if "message" in chunk and "content" in chunk["message"]:
                    yield chunk["message"]["content"]
                    
        except Exception as e:
            if self._current_model != self.backup_model:
                print(f"⚠️ Streaming failed, trying backup: {e}")
                self._current_model = self.backup_model
                yield from self.generate_stream(prompt, system_prompt, temperature, max_tokens)
            else:
                raise
    
    def chat(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """
        Multi-turn chat desteği.
        
        Args:
            messages: Mesaj listesi [{"role": "user/assistant/system", "content": "..."}]
            temperature: Yaratıcılık seviyesi
            max_tokens: Maksimum token
            
        Returns:
            Assistant yanıtı
        """
        try:
            response = self.client.chat(
                model=self._current_model,
                messages=messages,
                options={
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            )
            return response["message"]["content"]
        except Exception as e:
            if self._current_model != self.backup_model:
                self._current_model = self.backup_model
                return self.chat(messages, temperature, max_tokens)
            raise
    
    def get_status(self) -> dict:
        """Sistem durumunu döndür."""
        return {
            "primary_model": self.primary_model,
            "backup_model": self.backup_model,
            "current_model": self._current_model,
            "base_url": self.base_url,
            "primary_available": self.check_model_available(self.primary_model),
            "backup_available": self.check_model_available(self.backup_model),
        }
    
    def generate_with_image(
        self,
        prompt: str,
        image_path: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """
        Görsel ile birlikte LLM yanıtı üret (VLM desteği).
        
        Args:
            prompt: Kullanıcı prompt'u
            image_path: Görsel dosya yolu
            system_prompt: Sistem prompt'u (opsiyonel)
            temperature: Yaratıcılık seviyesi
            max_tokens: Maksimum token sayısı
            
        Returns:
            LLM yanıtı
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # Görsel ile birlikte mesaj
        messages.append({
            "role": "user",
            "content": prompt,
            "images": [image_path]
        })
        
        try:
            response = self.client.chat(
                model=self._current_model,
                messages=messages,
                options={
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            )
            return response["message"]["content"]
        except Exception as e:
            if self._current_model != self.backup_model:
                print(f"⚠️ Vision model başarısız, backup deneniyor: {e}")
                self._current_model = self.backup_model
                return self.generate_with_image(prompt, image_path, system_prompt, temperature, max_tokens)
            raise
    
    def generate_stream_with_image(
        self,
        prompt: str,
        image_path: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ):
        """
        Görsel ile streaming LLM yanıtı üret (VLM desteği).
        
        Yields:
            Token parçaları
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({
            "role": "user",
            "content": prompt,
            "images": [image_path]
        })
        
        try:
            stream = self.client.chat(
                model=self._current_model,
                messages=messages,
                options={
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
                stream=True,
            )
            
            for chunk in stream:
                if "message" in chunk and "content" in chunk["message"]:
                    yield chunk["message"]["content"]
                    
        except Exception as e:
            if self._current_model != self.backup_model:
                print(f"⚠️ Vision streaming failed, trying backup: {e}")
                self._current_model = self.backup_model
                yield from self.generate_stream_with_image(prompt, image_path, system_prompt, temperature, max_tokens)
            else:
                raise


# Singleton instance
llm_manager = LLMManager()
