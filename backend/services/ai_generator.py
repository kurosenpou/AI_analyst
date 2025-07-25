"""
AI Report Generator Service
Uses OpenRouter for multi-model LLM calls with fallback mechanisms
"""

import asyncio
import logging
from typing import Dict, Any, List
from services.openrouter_client import get_openrouter_client

logger = logging.getLogger(__name__)

class AIReportGenerator:
    """
    AI-powered report generator using OpenRouter multi-model approach
    """
    
    def __init__(self):
        self.client = get_openrouter_client()
        
        # Model assignments (will be used for debate system later)
        self.primary_model = "anthropic/claude-3-5-sonnet-20241022"
        self.secondary_model = "openai/gpt-4o"
        self.judge_model = "google/gemini-pro-1.5"
    
    async def generate_business_plan(
        self, 
        data: Dict[str, Any], 
        additional_context: str = ""
    ) -> str:
        """
        Generate comprehensive business plan using OpenRouter
        """
        
        prompt = self._create_business_plan_prompt(data, additional_context)
        
        try:
            response = await self.client.chat_completion(
                model=self.primary_model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert business analyst specializing in creating comprehensive business plans."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=2048,
                temperature=0.7
            )
            
            logger.info(f"Business plan generated successfully using {self.primary_model}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to generate business plan: {e}")
            raise
    
    async def generate_market_analysis(
        self, 
        data: Dict[str, Any], 
        additional_context: str = ""
    ) -> str:
        """
        Generate market analysis report using OpenRouter
        """
        
        prompt = self._create_market_analysis_prompt(data, additional_context)
        
        try:
            response = await self.client.chat_completion(
                model=self.secondary_model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a market research expert with deep knowledge of industry trends and competitive analysis."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=2048,
                temperature=0.6
            )
            
            logger.info(f"Market analysis generated successfully using {self.secondary_model}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to generate market analysis: {e}")
            raise
    
    async def generate_investment_summary(
        self, 
        data: Dict[str, Any], 
        additional_context: str = ""
    ) -> str:
        """
        Generate investment summary using OpenRouter
        """
        
        prompt = self._create_investment_summary_prompt(data, additional_context)
        
        try:
            response = await self.client.chat_completion(
                model=self.judge_model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a seasoned investment advisor with expertise in evaluating business opportunities and financial projections."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=2048,
                temperature=0.5
            )
            
            logger.info(f"Investment summary generated successfully using {self.judge_model}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to generate investment summary: {e}")
            raise
    
    def _create_business_plan_prompt(self, data: Dict[str, Any], context: str) -> str:
        """Create business plan generation prompt"""
        
        return f"""
Based on the provided data and context, create a comprehensive business plan including:

1. Executive Summary
2. Business Description
3. Market Analysis
4. Organization & Management
5. Service/Product Line
6. Marketing & Sales Strategy
7. Financial Projections
8. Risk Analysis

Data provided:
{data}

Additional context:
{context}

Please provide a detailed, professional business plan that addresses all these sections.
"""
    
    def _create_market_analysis_prompt(self, data: Dict[str, Any], context: str) -> str:
        """Create market analysis prompt"""
        
        return f"""
Conduct a thorough market analysis based on the provided data, including:

1. Market Size & Growth Potential
2. Target Market Segmentation
3. Competitive Landscape
4. Industry Trends
5. Market Entry Strategy
6. SWOT Analysis
7. Market Opportunities & Threats

Data provided:
{data}

Additional context:
{context}

Provide actionable insights and data-driven recommendations.
"""
    
    def _create_investment_summary_prompt(self, data: Dict[str, Any], context: str) -> str:
        """Create investment summary prompt"""
        
        return f"""
Create an investment summary and recommendation based on the provided data:

1. Investment Opportunity Overview
2. Financial Highlights
3. Key Success Factors
4. Risk Assessment
5. Return on Investment Analysis
6. Investment Recommendation
7. Exit Strategy Considerations

Data provided:
{data}

Additional context:
{context}

Provide a clear investment recommendation with supporting rationale.
"""
    
    async def test_models(self) -> Dict[str, bool]:
        """Test all configured models"""
        
        test_prompt = "Respond with 'Model test successful' if you can understand this message."
        
        results = {}
        
        for model_name, model_id in [
            ("primary", self.primary_model),
            ("secondary", self.secondary_model), 
            ("judge", self.judge_model)
        ]:
            try:
                response = await self.client.chat_completion(
                    model=model_id,
                    messages=[{"role": "user", "content": test_prompt}],
                    max_tokens=50,
                    temperature=0.1
                )
                results[model_name] = "successful" in response.lower()
                logger.info(f"Model {model_name} ({model_id}) test: {'PASS' if results[model_name] else 'FAIL'}")
                
            except Exception as e:
                results[model_name] = False
                logger.error(f"Model {model_name} ({model_id}) test failed: {e}")
        
        return results
