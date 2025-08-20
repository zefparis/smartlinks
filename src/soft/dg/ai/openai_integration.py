"""
OpenAI GPT-4 Integration for SmartLinks DG.

This module provides an asynchronous interface to interact with OpenAI's GPT-4 API.
"""
import os
import json
import logging
from typing import Dict, Any, List, Optional, Union
import openai
from openai import AsyncOpenAI
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class OpenAIIntegration:
    """Handles all interactions with OpenAI's GPT-4 API."""
    
    def __init__(self, api_key: str = None, model: str = "gpt-4-1106-preview"):
        """Initialize the OpenAI integration.
        
        Args:
            api_key: OpenAI API key. If not provided, will try to load from .env
            model: The OpenAI model to use (default: gpt-4-1106-preview)
        """
        load_dotenv()  # Load environment variables from .env
        
        self.model = model
        # Validate API key before constructing the client to avoid attribute errors
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not found. Please set OPENAI_API_KEY environment variable "
                "or pass the api_key parameter."
            )
        base_url = os.getenv("OPENAI_API_BASE")
        try:
            if base_url:
                self.client = AsyncOpenAI(api_key=self.api_key, base_url=base_url.rstrip("/"))
            else:
                self.client = AsyncOpenAI(api_key=self.api_key)
            # Try a simple request to validate the key
            # self.client.models.list() # This is a synchronous call, need an async alternative
            logger.info("OpenAI client initialized successfully.")
        except openai.AuthenticationError as e:
            logger.error("OpenAI API key is invalid or has expired. Please check your .env file.")
            raise ValueError(f"OpenAI authentication error: {e}") from e
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise
    
    async def ask_gpt4(
        self,
        prompt: str,
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> str:
        """Send a prompt to GPT-4 and return the response.
        
        Args:
            prompt: The user's prompt/message
            system_prompt: Optional system message to set the behavior
            temperature: Controls randomness (0.0 to 1.0)
            max_tokens: Maximum number of tokens to generate
            **kwargs: Additional arguments to pass to the API
            
        Returns:
            The generated text response from GPT-4
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
            
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            raise
    
    async def analyze_with_gpt4(
        self,
        context: Dict[str, Any],
        analysis_type: str = "generic",
        **kwargs
    ) -> Dict[str, Any]:
        """Analyze a context dictionary using GPT-4 with a specific analysis type.
        
        Args:
            context: The context data to analyze
            analysis_type: Type of analysis to perform (e.g., 'anomaly', 'optimization')
            **kwargs: Additional arguments to pass to ask_gpt4
            
        Returns:
            Dictionary containing the analysis results
        """
        system_prompts = {
            "anomaly": (
                "You are an AI assistant specialized in anomaly detection and analysis. "
                "Analyze the provided system metrics and logs to identify any anomalies, "
                "their potential impact, and recommended actions."
            ),
            "optimization": (
                "You are an AI assistant specialized in performance optimization. "
                "Analyze the provided system metrics and configuration to identify "
                "optimization opportunities and recommend specific actions."
            ),
            "reporting": (
                "You are an AI assistant specialized in generating clear, concise, and "
                "actionable reports. Summarize the key findings and provide "
                "recommendations based on the provided data."
            ),
            "generic": (
                "You are a helpful AI assistant. Analyze the provided information and "
                "provide a clear, concise response."
            )
        }
        
        system_prompt = system_prompts.get(analysis_type, system_prompts["generic"])
        
        # Convert context to a nicely formatted string
        context_str = json.dumps(context, indent=2, default=str)
        
        prompt = (
            f"Please analyze the following {analysis_type} context and provide insights:\n\n"
            f"{context_str}\n\n"
            "Provide your analysis in the following JSON format:\n"
            "{\n"
            "  \"summary\": \"Brief summary of the analysis\",\n"
            "  \"key_findings\": [\"list\", \"of\", \"key\", \"findings\"],\n"
            "  \"recommendations\": [\"list\", \"of\", \"recommendations\"],\n"
            "  \"confidence_score\": 0.0,\n"
            "  \"immediate_actions\": [\"list\", \"of\", \"immediate actions\"],\n"
            "  \"long_term_actions\": [\"list\", \"of\", \"long-term actions\"]\n"
            "}"
        )
        
        response = await self.ask_gpt4(
            prompt=prompt,
            system_prompt=system_prompt,
            response_format={"type": "json_object"},
            **kwargs
        )
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            logger.warning("Failed to parse GPT-4 response as JSON, returning as text")
            return {"raw_response": response}
    
    async def generate_report(
        self,
        data: Dict[str, Any],
        report_type: str = "executive_summary",
        format: str = "markdown",
        **kwargs
    ) -> str:
        """Generate a formatted report based on the provided data.
        
        Args:
            data: The data to include in the report
            report_type: Type of report to generate
            format: Output format (markdown, html, json)
            **kwargs: Additional arguments to pass to ask_gpt4
            
        Returns:
            The generated report in the requested format
        """
        report_types = {
            "executive_summary": "a concise executive summary highlighting key points",
            "detailed_analysis": "a detailed analysis with supporting data",
            "incident_report": "a comprehensive incident report with timeline and impact analysis"
        }
        
        report_instructions = report_types.get(report_type, report_types["executive_summary"])
        
        prompt = (
            f"Generate {report_instructions} based on the following data. "
            f"Format the output as {format.upper()}.\n\n"
            f"{json.dumps(data, indent=2, default=str)}"
        )
        
        return await self.ask_gpt4(prompt=prompt, **kwargs)
